# Ethics and limitations

**This is a research prototype. It is not a validated diagnostic device and makes no claim of clinical readiness.**

## Data ethics

- Only de-identified, openly licensed (CC0) public data were used, and only their public metadata in the build session. No restricted data, credentials or patient-level files are in this repository (`.gitignore` blocks EEG/MRI formats and `data/raw|interim|processed|external`).
- Restricted datasets (PPMI, OASIS-3, ADNI) were not accessed and no access control was bypassed. Using them requires each dataset's application and data-use agreement, and their terms (no re-identification, secure storage, acknowledgement and publication policies) apply.
- **ds002778 steward request:** the maintainers ask to be emailed before a manuscript uses the data and specifically caution against ML classification of PD vs HC on this small cohort. Contact them before any publication. Here the cohort is intended only as a small external test set, reported with wide confidence intervals and explicit caveats.

## Limitations of the completed work (E0, E1)

- **Confounding by age.** In ds007526 healthy controls are about 5 years younger than PD participants. Age alone reaches ROC-AUC ≈ 0.61-0.68, so most of the E0 signal is demographic and says nothing about neurophysiology.
- **Small, imbalanced cohort.** 144 participants (116 PD / 28 HC): wide intervals, and threshold metrics at 0.5 are unstable (e.g. the SVM predicts everyone as PD at 0.5).
- **Single site, single visit.** No external cohort has been tested for E0/E1; they are within-cohort estimates only.
- **Selection.** PD inclusion criteria (H&Y ≤ 3, MoCA ≥ 21) restrict severity range, so E1 does not generalise to advanced PD.
- **Undocumented units/conditions.** `disease_duration` unit and medication state at UPDRS assessment are not documented in the files read.
- **Mean-baseline artefact.** The negative Spearman of the training-mean regressor in E1 is a known artefact of leave-out mean prediction, not a finding.

## Limitations of the project as a whole

- No EEG or MRI signal was analysed: the signal files were not downloadable in the build environment. Every EEG, MRI, explainability, multimodal and external-validation component is therefore **implemented but not run**, or **planned**.
- No Alzheimer's component has been executed or validated.
- Unit tests use hand-built fixtures to test code; they are not evidence about disease.
- Novelty has not been established. A defensible contribution (leakage-safe cross-cohort EEG validation with quantified domain shift between two independent PD cohorts) is designed here, but no claim of novelty or performance should be made before the EEG experiments are run and reviewed.
- Sex and age are included as covariates because they are available and clinically relevant; subgroup performance analyses need larger cohorts than those available.
