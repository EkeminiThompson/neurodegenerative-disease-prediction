# Ethics and limitations

**This is a research prototype. It is not a validated diagnostic device and makes no claim of clinical readiness.**

## Data ethics

- Only de-identified, openly licensed (CC0) public data were used, and only their public metadata in the build session. No restricted data, credentials or patient-level files are in this repository (`.gitignore` blocks EEG/MRI formats and `data/raw|interim|processed|external`).
- Restricted datasets (PPMI, OASIS-3, ADNI) were not accessed and no access control was bypassed. Using them requires each dataset's application and data-use agreement, and their terms (no re-identification, secure storage, acknowledgement and publication policies) apply.
- **ds002778 steward request:** the maintainers ask to be emailed (arockhil@uoregon.edu) before a manuscript uses the data and specifically describe ML classification of PD vs HC on this small cohort as problematic. Here it is used only as an external test set for a model trained elsewhere, never as a training set, with wide confidence intervals and explicit caveats, and the maintainers will be contacted before any submission.
- **ds007526 authors:** the dataset page asks users to contact the authors; they have published their own EEG-based analysis of this cohort. Contact them before any submission.

## Limitations of the completed work (E0, E1)

- **Age confounding (confirmed by A3).** In an age-matched subset (n=54) clinical AUCs are indistinguishable from chance (all CIs include 0.5), so the E0 signal is demographic. Sub-0.5 point estimates are cross-validation artefacts of noise in tiny samples, not information.
- Healthy controls in ds007526 are about 5 years younger than PD participants (60.8 vs 66.1); age alone reaches ROC-AUC 0.61-0.68 in E0.
- **Small, imbalanced cohort.** 144 participants (116 PD / 28 HC): wide intervals, and threshold metrics at 0.5 are unstable (e.g. the SVM predicts everyone as PD at 0.5).
- **Single site; cross-sectional analyses.** No external cohort has been tested for E0/E1; they are within-cohort estimates only. A follow-up subset (n=39 PD) exists in `sourcedata/` and is summarised descriptively only.
- **Selection.** PD inclusion criteria (H&Y ≤ 3, MoCA ≥ 21) restrict severity range, so E1 does not generalise to advanced PD.
- **Undocumented units/conditions.** `disease_duration` unit and medication state at UPDRS assessment are not documented in the files read.
- **Mean-baseline artefact.** The negative Spearman of the training-mean regressor in E1 is a known artefact of leave-out mean prediction, not a finding.

## Limitations of the project as a whole

- Sex-subgroup results (A4) rest on 12-15 healthy controls per sex and are exploratory.
- No EEG or MRI signal was analysed: the signal files were not downloadable in the build environment. Every EEG, MRI, explainability, multimodal and external-validation component is therefore **implemented but not run**, or **planned**.
- No Alzheimer's component has been executed or validated.
- Unit tests use hand-built fixtures to test code; they are not evidence about disease.
- Novelty has not been established. A defensible contribution (leakage-safe cross-cohort EEG validation with quantified domain shift between two independent PD cohorts) is designed here, but no claim of novelty or performance should be made before the EEG experiments are run and reviewed.
- Sex and age are included as covariates because they are available and clinically relevant; subgroup performance analyses need larger cohorts than those available.
