# Methodology

## Design principle

Every claim in this repository must be traceable to code that ran on real participant-level
data. Components that could not be run are labelled "implemented, not run" or "planned".

## Pipeline

1. **Metadata audit** (`scripts/fetch_metadata.py`, `scripts/audit_metadata.py`): public BIDS metadata, counts and checksums.
2. **EEG preprocessing** (`ndpred.preprocessing.eeg`): identical for all cohorts. Non-scalp channels that the cohorts type as EEG (EOG1-4, VREF, EXG1-8, Status) are dropped first so they cannot contaminate the common-average reference. Then: 1-45 Hz zero-phase FIR band-pass, mains notch from the sidecar, resample to 250 Hz, common-average reference, 4 s non-overlapping windows, peak-to-peak rejection (200 µV). Rejection counts are logged; rejected windows are dropped, never repaired.
3. **Feature extraction** (`ndpred.features.eeg`): band powers, relative powers, spectral entropy, peak alpha frequency, Hjorth parameters, ratios. Window-level values are collapsed to **one vector per recording by the median over windows**, averaged over the 31 scalp channels shared by both cohorts (`core_*`) and over 10-20 regions (`reg_*`; Cz omitted because it is the recording reference in ds007526) for cross-cohort comparability, so windows of one person cannot be split across train/test.
4. **Models** (`ndpred.models.baselines`): logistic regression, random forest, RBF-SVM, XGBoost, LightGBM, each in a pipeline of median imputation, standardisation, optional `SelectKBest`, estimator. Class imbalance via class weights (`scale_pos_weight` for XGBoost). Ridge and random-forest regressors for severity.
5. **Evaluation** (`ndpred.evaluation`): repeated stratified group k-fold (groups = participant); each participant's prediction is the mean of its out-of-fold predictions over repeats; 95% CIs by resampling whole participants (2,000 bootstrap draws). Metrics: accuracy, balanced accuracy, precision, recall/sensitivity, specificity, F1, ROC-AUC, PR-AUC, Brier score, expected calibration error, confusion counts; MAE, Spearman and (for integer targets) weighted/quadratic kappa for severity.
6. **External validation** (`ndpred.evaluation.external`): fit on the development cohort only; predict the external cohort once. Domain shift is quantified before any disease label is used: standardized mean differences per feature and a cross-validated domain-classifier AUC (cohort A vs B). Results are reported with raw features and with label-free per-cohort z-scoring side by side, because the latter is transductive.
7. **Fusion** (`ndpred.fusion.late`): per-modality models combined by averaging probabilities over modalities actually observed for each participant; no modality is imputed.
8. **Explainability** (`ndpred.explainability.shap_utils`): SHAP (tree, linear, kernel fallback) on the fitted pipeline with training-set background data. Implemented; not run on real EEG features.
9. **Tracking** (`ndpred.utils.tracking`): every run appends a JSON line (config, config hash, environment, metrics) to `reports/results/runs.jsonl`.

## Leakage controls

- Splits are by participant. A unit test fits recordings-per-participant data and asserts no participant appears in both train and test.
- Imputation, scaling and feature selection are inside the sklearn pipeline and re-fit on each training fold.
- Label-defined clinical variables are excluded from classification features (see `data_dictionary.md`).
- The external cohort is never used for tuning, selection or scaling parameters (except the explicitly separate, label-free per-cohort z-scoring condition).

## What the code does not do yet

- No MRI feature extraction or Alzheimer's pipeline exists (planned; access-gated).
- Deep models (EEGNet, CNN, transformers) are not implemented. With 144 and 31 participants they are not justified, and the dataset steward of ds002778 advises against ML on that cohort at all.
- Notebooks 02 and 04 are placeholders because the AD data and EEG signals were unavailable.
- No time-to-event or predictive longitudinal model. ds007526 has follow-up data for 39 PD participants (descriptive summary only; medication state at assessment undocumented); too few for survival or progression modelling.
- Nested cross-validation (inner grouped 3-fold grid search) has been run once, for the clinical-only baselines (A5), via `scripts/run_clinical_extended.py`; it has not yet been applied to EEG features.
