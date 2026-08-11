# Maintainer Evidence

> Local-first Python CLI for reproducible, privacy-aware maintenance evidence from a Git checkout.

`v0.1.0 · Alpha` · Python 3.10+ · MIT · no runtime dependencies

Maintainer Evidence helps an open-source maintainer review and document real maintenance signals before sharing them with a funder, program, or community. It reads a local Git checkout and produces a JSON report plus a Markdown report that a human can inspect.

## Try it in 60 seconds

```bash
git clone https://github.com/5166li-beep/compassing-oss-maintainer-kit.git
cd compassing-oss-maintainer-kit
python -m pip install .
maintainer-evidence --repo /path/to/your/repo --out evidence --redact-authors
```

The command writes `evidence/evidence.json` and `evidence/evidence.md`. Review both files before sharing them: Git history can contain author names and commit subjects even when author redaction is enabled for the report.

Use `--since-days 90` when you want a shorter lookback window. The command accepts a repository path; it does not need the target repository to be hosted on GitHub.

## What it reports

- commits, active days, authors, and recent tags over a configurable lookback;
- whether README, license, contributing, security, code-of-conduct, and changelog files are present;
- GitHub Actions workflow files, common ecosystem manifests, and a test directory;
- JSON and Markdown output, with optional author redaction.

The output is evidence to review, not an eligibility score. It does not invent stars, downloads, users, or maintainer permissions.

## Suitable for / not suitable for

Suitable for maintainers who need a reproducible, reviewable snapshot of local maintenance signals before sharing it with another person or organization.

Not suitable for live GitHub analytics, a hosted dashboard, an eligibility decision, permission verification, or any claim that requires current external metrics. Keep those measurements separate and record their source and timestamp.

## Privacy and source boundaries

- The collector reads the local Git checkout and public-facing repository files.
- It does not call GitHub, upload repository contents, or require credentials.
- Do not put secrets, customer data, identity documents, or private roadmap material in this repository or in generated evidence.
- Inspect generated reports before sharing them, even when using `--redact-authors`.

## Project status and feedback

This project was just published. It currently has local tests and a read-only GitHub Actions workflow; there are no claims here about external users, downloads, or outside contributors.

- [Open an Issue](https://github.com/5166li-beep/compassing-oss-maintainer-kit/issues) for a reproducible bug or a field that seems misleading.
- [Join the early feedback discussion](https://github.com/5166li-beep/compassing-oss-maintainer-kit/discussions/1) with your Python version, operating system, repository shape, command, and result. Do not paste private repository contents, secrets, or identity data.
- [Read the v0.1.0 release notes](https://github.com/5166li-beep/compassing-oss-maintainer-kit/releases/tag/v0.1.0).

If this becomes useful to your maintenance workflow after you try it, a GitHub star can help other maintainers discover it. A failure report is more valuable than a drive-by star.

## Development

From a checkout, install the package first, then run the tests:

```bash
python -m pip install .
python -m unittest discover -s tests -v
```

If you only want to run the tests without installing, use:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
