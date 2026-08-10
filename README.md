# Maintainer Evidence

Maintainer Evidence creates a small, reproducible evidence pack from a local
Git checkout. It helps an open-source maintainer review and document real
maintenance signals before sharing them with a funder, program, or community.

The tool is deliberately local-first: it reads Git history and public-facing
repository files, does not call GitHub, does not upload anything, and does not
need credentials.

## What it measures

- commits, active days, authors, and recent tags in a configurable lookback;
- the presence of README, license, contributing, security, code-of-conduct,
  and changelog documents;
- GitHub Actions workflow files;
- common ecosystem manifests and a test directory.

The output is evidence, not an eligibility decision. It does not invent stars,
downloads, users, or maintainer permissions. Add registry or GitHub metrics
only when you can verify them independently.

## Quick start

```bash
python -m pip install .
maintainer-evidence --repo . --out evidence --redact-authors
```

This writes `evidence/evidence.json` and `evidence/evidence.md`. Review both
files before sharing them. Use `--since-days 90` for a shorter window.

## GitHub Actions

The included workflow runs on pushes, pull requests, and a weekly schedule.
It uploads a redacted evidence artifact and uses only `contents: read`.

## Design boundaries

This project intentionally avoids GitHub API tokens and external network calls
in the collector. A future integration may fetch public repository metrics, but
it must keep the fetched data separate from local evidence and make the source
and timestamp explicit.

Do not place secrets, customer data, identity documents, or private roadmap
material in this repository or in generated evidence.

## Development

```bash
python -m unittest discover -s tests -v
```

Contributions and reproducible bug reports are welcome. See
`CONTRIBUTING.md` and `SECURITY.md`.

## License

MIT. See `LICENSE`.
  
