# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-10

### Added
- Dataset audit of two open, CC0 Parkinson's disease EEG cohorts, OpenNeuro ds007526 v1.0.2 and ds002778 v1.0.5, with dataset manifests (version, mirror commit, checksum) and metadata loaders.
- Leakage-safe evaluation framework: participant-grouped repeated stratified cross-validation, participant-level bootstrap confidence intervals, paired model comparison with Holm correction, calibration metrics, nested cross-validation and age-matched sensitivity analysis.
- Real-data clinical analyses on ds007526 metadata: PD vs healthy-control classification from age, sex and MoCA (E0), UPDRS part III severity within PD (E1), and extended analyses A1-A5.
- Independent-cohort test (X1): age and sex models fitted on ds007526 and applied to the age-balanced cohort ds002778.
- EEG preprocessing and feature-extraction pipeline (MNE), external-validation utilities, late-fusion and SHAP modules, JSONL run logging, and unit tests (19) with continuous integration.
- Two manuscripts in `paper/`: age imbalance and clinical-metadata classification, and a verified audit of the two open EEG cohorts.
- Literature check and novelty assessment (`docs/literature_and_novelty.md`).

### Notes
- No EEG or MRI signal data have been analysed in this release. Restricted datasets (PPMI, OASIS-3, ADNI) were not accessed.
