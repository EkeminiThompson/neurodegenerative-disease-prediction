# Contributing

Thank you for your interest. This is a research codebase; correctness and reproducibility come before new features.

## Principles
- **Real data only.** No synthetic or fabricated data or results. Unit tests may use small hand-built fixtures to test code, never to report findings.
- **No leakage.** Splits are participant-grouped; preprocessing, feature selection and tuning happen inside training folds.
- **Respect data access rules.** Do not commit raw or derived patient-level files from restricted datasets (PPMI, OASIS-3, ADNI), and follow the stewards' requests for open datasets (see `docs/ethics_and_limitations.md`).
- **Report uncertainty.** Give confidence intervals and state limitations; do not claim external validation unless the test cohort is truly independent.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,eeg,boost,explain]"
```

## Before opening a pull request
```bash
ruff check src scripts tests
pytest -q
```
Add or update tests for behaviour changes, and add an entry under "Unreleased" in `CHANGELOG.md`.

## Reporting issues
Open a GitHub issue with the steps to reproduce, the data version and the exact command used.
