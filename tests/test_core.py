from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from maintainer_evidence.core import collect_evidence, render_markdown, write_evidence


def make_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "README.md").write_text("# Example\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "CONTRIBUTING.md").write_text("Please open a pull request.\n", encoding="utf-8")
    (root / "SECURITY.md").write_text("Report security issues privately.\n", encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_example.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    env = {
        "GIT_AUTHOR_NAME": "Test Maintainer",
        "GIT_AUTHOR_EMAIL": "maintainer@example.invalid",
        "GIT_COMMITTER_NAME": "Test Maintainer",
        "GIT_COMMITTER_EMAIL": "maintainer@example.invalid",
    }
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Test Maintainer", "-c", "user.email=maintainer@example.invalid", "commit", "-qm", "initial"],
        check=True,
        env={**__import__("os").environ, **env},
    )


class EvidenceTests(unittest.TestCase):
    def test_collects_local_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_git_repo(root)
            evidence = collect_evidence(root, since_days=180)
            self.assertEqual(evidence["git_activity"]["commit_count"], 1)
            self.assertEqual(evidence["maintenance_signals"]["workflow_count"], 1)
            self.assertTrue(evidence["maintenance_signals"]["has_tests"])
            self.assertEqual(evidence["maintenance_signals"]["public_documents"]["license"], "LICENSE")

    def test_redacts_authors_and_writes_two_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_git_repo(root)
            evidence = collect_evidence(root, redact_authors=True)
            self.assertEqual(evidence["git_activity"]["authors"], ["[redacted]"])
            output = root / "evidence"
            json_path, markdown_path = write_evidence(evidence, output)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["schema_version"], 1)
            self.assertNotIn("Test Maintainer", json_path.read_text(encoding="utf-8"))
            self.assertTrue(markdown_path.is_file())

    def test_markdown_is_explicit_about_limits(self) -> None:
        evidence = {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "repository": "demo",
            "git_activity": {
                "lookback_days": 180,
                "commit_count": 0,
                "active_days": 0,
                "authors": [],
                "tag_count": 0,
                "commits": [],
            },
            "maintenance_signals": {
                "public_documents": {key: None for key in ("readme", "license", "contributing", "code_of_conduct", "security", "changelog")},
                "workflow_count": 0,
                "ecosystem_manifests": [],
                "has_tests": False,
            },
        }
        rendered = render_markdown(evidence)
        self.assertIn("not a claim of program eligibility", rendered)
        self.assertIn("No commits found", rendered)


if __name__ == "__main__":
    unittest.main()
  
