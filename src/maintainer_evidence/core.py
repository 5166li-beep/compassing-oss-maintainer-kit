"""Collect and render local, reproducible open-source maintenance signals.

The collector intentionally uses only the local Git checkout and filesystem.
It does not call GitHub, upload data, or require credentials. This makes the
result suitable for review before an operator decides whether to share it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


_MAINTENANCE_FILES = {
    "readme": ("README", "README.md", "README.rst", "README.txt"),
    "contributing": ("CONTRIBUTING.md", "CONTRIBUTING.rst", ".github/CONTRIBUTING.md"),
    "code_of_conduct": ("CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md"),
    "security": ("SECURITY.md", ".github/SECURITY.md"),
    "license": ("LICENSE", "LICENSE.md", "COPYING"),
    "changelog": ("CHANGELOG.md", "CHANGES.md", "HISTORY.md"),
}


def _git(repo: Path, *args: str) -> str:
    """Run a read-only Git command and return stdout.

    A clear error is raised for a non-Git directory; individual optional
    signals can handle missing refs without hiding a broken repository.
    """

    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _first_existing(repo: Path, candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        if (repo / candidate).is_file():
            return candidate
    return None


def _parse_commit_line(line: str, redact_authors: bool) -> dict[str, str]:
    commit, date, author, subject = (line.split("\t", 3) + [""] * 4)[:4]
    return {
        "commit": commit,
        "date": date,
        "author": "[redacted]" if redact_authors else author,
        "subject": subject,
    }


def collect_git_activity(
    repo: Path,
    *,
    since_days: int = 180,
    redact_authors: bool = False,
) -> dict[str, Any]:
    """Collect commit and tag signals from the selected lookback window."""

    if since_days < 1:
        raise ValueError("since_days must be at least 1")
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    raw = _git(
        repo,
        "log",
        "--date=iso-strict",
        "--format=%H%x09%ad%x09%an%x09%s",
        f"--since={cutoff.isoformat()}",
    )
    commits = [_parse_commit_line(line, redact_authors) for line in raw.splitlines() if line]
    active_dates = sorted({entry["date"][:10] for entry in commits})

    tags_raw = _git(
        repo,
        "for-each-ref",
        "--sort=-creatordate",
        "--format=%(refname:short)\t%(creatordate:iso-strict)",
        "refs/tags",
    )
    tags = []
    for line in tags_raw.splitlines():
        if not line:
            continue
        name, _, created = line.partition("\t")
        tags.append({"name": name, "created": created})

    authors = sorted({entry["author"] for entry in commits})
    return {
        "lookback_days": since_days,
        "cutoff": cutoff.isoformat(),
        "commit_count": len(commits),
        "active_days": len(active_dates),
        "active_dates": active_dates,
        "authors": authors,
        "commits": commits,
        "tag_count": len(tags),
        "recent_tags": tags[:20],
    }


def collect_maintenance_signals(repo: Path) -> dict[str, Any]:
    """Inspect public-facing maintenance files and automation, locally."""

    files = {
        key: _first_existing(repo, candidates)
        for key, candidates in _MAINTENANCE_FILES.items()
    }
    workflows_dir = repo / ".github" / "workflows"
    workflows = sorted(
        str(path.relative_to(repo))
        for path in workflows_dir.glob("*")
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    ) if workflows_dir.is_dir() else []

    ecosystem_manifests = [
        name
        for name in (
            "pyproject.toml",
            "setup.py",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "composer.json",
        )
        if (repo / name).is_file()
    ]
    return {
        "public_documents": files,
        "workflow_files": workflows,
        "workflow_count": len(workflows),
        "ecosystem_manifests": ecosystem_manifests,
        "has_tests": any(
            (repo / directory).is_dir()
            for directory in ("tests", "test", "spec", "__tests__")
        ),
    }


def collect_evidence(
    repo: str | Path,
    *,
    since_days: int = 180,
    redact_authors: bool = False,
) -> dict[str, Any]:
    """Build a JSON-serialisable evidence report for *repo*."""

    root = Path(repo).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"repository does not exist: {root}")
    if _git(root, "rev-parse", "--is-inside-work-tree") != "true":
        raise ValueError(f"not a Git work tree: {root}")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": root.name,
        "repository_path": str(root),
        "git_activity": collect_git_activity(
            root,
            since_days=since_days,
            redact_authors=redact_authors,
        ),
        "maintenance_signals": collect_maintenance_signals(root),
    }


def render_markdown(evidence: dict[str, Any]) -> str:
    """Render a concise, reviewable Markdown representation."""

    activity = evidence["git_activity"]
    signals = evidence["maintenance_signals"]
    docs = signals["public_documents"]
    lines = [
        f"# Maintenance evidence: `{evidence['repository']}`",
        "",
        "> Generated from a local Git checkout. This report is evidence, not a claim of program eligibility.",
        "",
        f"- Generated: `{evidence['generated_at']}`",
        f"- Lookback: `{activity['lookback_days']} days`",
        f"- Commits in window: **{activity['commit_count']}**",
        f"- Active days in window: **{activity['active_days']}**",
        f"- Distinct authors in window: **{len(activity['authors'])}**",
        f"- Tags found: **{activity['tag_count']}**",
        "",
        "## Repository hygiene signals",
        "",
    ]
    for key in ("readme", "license", "contributing", "code_of_conduct", "security", "changelog"):
        lines.append(f"- `{key}`: `{docs[key] or 'missing'}`")
    lines.extend([
        f"- GitHub Actions workflow files: **{signals['workflow_count']}**",
        f"- Ecosystem manifests: `{', '.join(signals['ecosystem_manifests']) or 'none detected'}`",
        f"- Test directory present: **{'yes' if signals['has_tests'] else 'no'}**",
        "",
        "## Recent commits",
        "",
    ])
    for commit in activity["commits"][:20]:
        lines.append(f"- `{commit['date'][:10]}` `{commit['commit'][:12]}` {commit['subject']}")
    if not activity["commits"]:
        lines.append("- No commits found in the selected lookback window.")
    lines.extend([
        "",
        "## Sharing checklist",
        "",
        "- Verify that the repository URL is public and that the applicant has the stated maintainer permissions.",
        "- Add only metrics that can be verified from GitHub or the package registry.",
        "- Do not include secrets, private customer data, or confidential roadmap information.",
    ])
    return "\n".join(lines) + "\n"


def write_evidence(evidence: dict[str, Any], output_dir: str | Path) -> tuple[Path, Path]:
    """Write JSON and Markdown reports and return their paths."""

    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "evidence.json"
    markdown_path = target / "evidence.md"
    json_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(evidence), encoding="utf-8")
    return json_path, markdown_path
  
