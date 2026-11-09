# Experimental protocol

Analyses are fixed here before any EEG-based result exists, so that the EEG experiments
cannot be tuned after seeing outcomes. Anything run outside this list is labelled
"exploratory".

## Completed (metadata only, real data)

| ID | Question | Data | Features | Target | Protocol |
|---|---|---|---|---|---|
| E0 | How well do basic demographics and cognition separate PD from HC, and how much is age confounding? | ds007526, n=144 | `age`; `age+sex+moca` | PD vs HC | 5-fold stratified group CV × 20 repeats; 5 models; 2,000-draw participant bootstrap |
| E1 | Can age, sex, MoCA, disease duration and LEDD predict UPDRS-III within PD? | ds007526 PD with UPDRS-III, n=113 | those five | UPDRS part III (points) | same CV; ridge and random forest vs a training-mean baseline; MAE and Spearman |
| A1 | Do models differ? | as E0 complete cases, n=140 | `age+sex+moca` | PD vs HC | 10 repeats; paired participant-bootstrap AUC differences (2,000 draws), Holm correction |
| A2 | Calibration | as A1 | `age+sex+moca` | PD vs HC | reliability curves (5 bins), Brier, ECE |
| A3 | How much of E0 is age confounding? | 1:1 age-matched subset (caliper 3 y), n=54 | age; sex+moca; age+sex+moca | PD vs HC | same CV |
| A4 | Subgroup performance | out-of-fold predictions of A1 | by sex | | participant bootstrap (1,000 draws) |
| A5 | Does tuning help? | as A1 | `age+sex+moca` | PD vs HC | nested: outer 5-fold x3, inner grouped 3-fold grid (logreg C; RF leaf/depth) |

## Defined, not run (require the EEG signals)

| ID | Question | Protocol |
|---|---|---|
| P1 | Within-cohort PD vs HC from resting EEG (ds007526); **must also be reported on the age-matched subset (A3 design)** | `scripts/extract_eeg_features.py` then `scripts/run_eeg_experiments.py`; feature sets: clinical, EEG region/global, clinical+EEG; k=20 selected features inside folds |
| P2 | External validation ds007526 → ds002778 (one direction; training on ds002778's 15 patients is excluded from the primary analysis following its maintainers' advice; `--include-reverse` is exploratory) | `scripts/run_external_validation.py`; features over the 31 shared scalp channels (`core_*`) and region-level (`reg_*`); raw and per-cohort z-scored conditions; report internal vs external AUC, AUC drop, calibration, domain-classifier AUC, top standardized mean differences |
| P3 | Medication state (ds002778 only) | ON vs OFF sessions as a within-participant sensitivity analysis; descriptive only (n=15) |
| P4 | Resting vs walking EEG (ds007526) | extract `--task walk` features and repeat P1; primary analysis stays resting state. Non-scalp channels (EOG1-4, VREF; EXG1-8, Status) are always dropped before re-referencing |
| P6 | Descriptive longitudinal summary (ds007526, n=39 follow-ups) | `scripts/longitudinal_descriptives.py`; no predictive claim (medication state undocumented) |
| P5 | Explainability | SHAP on the best pre-specified model; plausibility discussed against known PD EEG findings (e.g. beta, theta/alpha changes) without causal claims |

## Primary outcome definition

Primary metric: ROC-AUC with a 95% participant-level bootstrap CI. Secondary: PR-AUC,
balanced accuracy, sensitivity, specificity at threshold 0.5 (no tuning on test data),
Brier score and expected calibration error. Every reported number states dataset,
participant count, split strategy and feature set.

## Stopping rules and honesty rules

- If a cohort has fewer than 10 participants in a class after QC, the experiment is reported as infeasible rather than run.
- If domain-classifier AUC between cohorts is ≥ 0.9, external performance is interpreted as a domain-shift finding first.
- Negative and null results are reported.

## Alzheimer's (planned)

After access is granted: map diagnostic labels from the data dictionaries, define the
shared variable set between OASIS-3 and ADNI, audit domain shift, then follow the same
CV and external-validation protocol with FreeSurfer-derived regional volumes plus clinical
variables. Longitudinal progression is evaluated with time-to-event methods, not
cross-sectional proxies.
