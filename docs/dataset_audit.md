# Dataset audit

Audit date: 2026-11-08. Every number marked **verified** is reproduced by
`python scripts/fetch_metadata.py && python scripts/audit_metadata.py` (output in
`data/manifests/*.json`, including the SHA-256 of each `participants.tsv` and the exact
mirror commit). Items marked **not verified** were not checked against source in this
session and must not be quoted as facts.

## Access status summary

| Dataset | Disease | Modality | Access | Accessed in build session? |
|---|---|---|---|---|
| OpenNeuro ds007526 | PD | EEG | Open, CC0 | **Metadata only.** EEG signals were not downloadable (sandbox blocked the storage host). |
| OpenNeuro ds002778 | PD | EEG | Open, CC0 | **Metadata only.** Same reason. |
| PPMI | PD | Clinical, MRI, biomarkers | Application + Data Use Agreement + Publications Policy; investigator-level | No. Not bypassed. |
| OASIS-3 | AD | MRI, PET, clinical | NITRC-IR registration, staff review, data use agreement | No. Not bypassed. |
| ADNI | AD | MRI, PET, biomarkers, clinical | Application + Data Use Agreement via LONI | No. Not bypassed. |
| Alzheimer's Disease Data Initiative | AD | Various | Portal (AD Workbench) | **Not investigated.** |

## ds007526: PD-EEG, resting-state and walking EEG

- Source: https://openneuro.org/datasets/ds007526, version 1.0.2 (changelog: 1.0.0 2026-03-18, 1.0.1 2026-05-07, 1.0.2 2026-06-08 "additional clinical data").
- DOI: `10.18112/openneuro.ds007526.v1.0.2`. Licence: CC0. Site: Neurology Institute, Tel Aviv Sourasky Medical Center. Authors: Katzir, Vered, Maidan.
- Size (OpenNeuro page): 1,823 files, 4.26 GB; 1 session; tasks `rest` and `walk`; BIDS validation passes with 5,430 warnings. Acquisition: 64-channel EGI Geodesic System 400 (65 channels recorded incl. EOG1-4 and VREF, typed `EEG` in `channels.tsv`; Cz is the recording reference), 10-20 labels.
- **Please contact the authors.** The dataset page's "How to Acknowledge" field says "Please contact the authors" (Inbal Maidan, inbalm@tlvmc.gov.il; Daniel Vered, vereddan@tlvmc.gov.il). The data owners have themselves published an EEG-based clustering analysis of this cohort (related article below); any overlap should be discussed with them before submission.
- Related publication (from `dataset_description.json`): "Electroencephalography-Based Clustering Reveals Robust Neurophysiological Subtypes in Parkinson's Disease", https://doi.org/10.1002/mds.70348.
- Participants (**verified**): 144 = 116 PD + 28 HC.
- Recordings (**verified**): 277 = 144 resting-state (sitting, eyes open, ~4 min) + 133 treadmill-walking (~4 min); one `.set` file each. Example sidecar: 65 EEG channels, 250 Hz, 50 Hz mains.
- Clinical variables and non-missing counts (**verified**): age 144, sex 144, MoCA 140, UPDRS part III 139, UPDRS total 139, disease duration 116 (PD only), LEDD 115 (PD only), PIGD 113, tremor-dominant score 113, CTT 135.
- Not present in `participants.tsv` (**verified**): Hoehn & Yahr. The README lists H&Y ≤ 3 and MoCA ≥ 21 as PD inclusion criteria, which restricts severity range.
- Undocumented in what was read: unit of `disease_duration` (values suggest months; **not verified**), medication state at recording and at UPDRS assessment, eye state labelling in the walking task, EEG reference.
- Group imbalance: HC are younger on average (60.8 vs 66.1 years) and 28 vs 116 is strongly imbalanced; sex 15F/13M (HC) vs 44F/72M (PD).
- Suitability: development cohort for the PD EEG pipeline (largest open PD EEG cohort found here) or external test cohort. **Additional clinical data in `sourcedata/clinical_data/` (verified):** `full_UPDRS_data.tsv` (item-level MDS-UPDRS parts 1-4, 117 PD rows, 115 of which map to `participants.tsv` by `subject_id`; no Hoehn & Yahr column) and `longitudinal_clinical_data.tsv` (39 PD participants, all matched; EEG date, follow-up date, UPDRS total and part III, MoCA, LEDD; mean interval 2.2 years, range 0.4-5.7). *Correction:* an earlier version of this audit stated that no longitudinal data exist; that was wrong because `sourcedata/` had not been inspected. Descriptive summary: `reports/tables/longitudinal_descriptives_ds007526.csv`. Medication state at either assessment is not documented.

## ds002778: UC San Diego resting-state EEG in PD

- Source: https://openneuro.org/datasets/ds002778, version 1.0.5 (328 files, 545 MB; 3 sessions: hc, on, off), DOI `10.18112/openneuro.ds002778.v1.0.5`, CC0. Authors: Rockhill, Jackson, George, Aron, Swann.
- Cited papers (from README): Jackson et al., eNeuro 2019, 10.1523/ENEURO.0151-19.2019; Swann et al., Ann Neurol 2015, 10.1002/ana.24507; George et al., NeuroImage Clin 2013, 10.1016/j.nicl.2013.07.013.
- Participants (**verified**): 31 = 15 PD + 16 HC. Group is encoded in the participant ID prefix (`sub-hc*`, `sub-pd*`), consistently across all 31 rows.
- Recordings (**verified**): 46 resting-state `.bdf` files = 16 HC + 15 PD ON medication + 15 PD OFF medication. Example sidecar: BioSemi, 40 EEG channels, 512 Hz, 60 Hz mains.
- Clinical variables (**verified**): age, gender, handedness, MMSE, NAART for all 31; disease duration (years) for PD; per-session `beh` JSON with UPDRS subscores, total UPDRS, Beck score and **Hoehn & Yahr** for PD.
- H&Y distribution (**verified**): only two levels (2.0: 15 sessions, 3.0: 15 sessions). 12 of 15 PD participants have the same H&Y ON and OFF. Severity classification on 15 participants with two levels is not defensible; H&Y is reported descriptively only.
- Data-steward statements (README): (1) contact the maintainers before submitting a manuscript that uses the data; (2) UPDRS was rated by trained lab personnel, not a board-certified neurologist; (3) ML classification of PD vs HC on this dataset is explicitly described as problematic because of the small number of patients. This project respects these: ds002778 is used only as a small external test cohort with wide confidence intervals, and the maintainers must be contacted before publication.
- Data notes from the page and its comments: (a) channels `EXG1`-`EXG8` (eye and mastoid channels) are typed `EEG` in `channels.tsv` and `Status` is a trigger channel; the preprocessing drops them; (b) the maintainers state that the data are not preprocessed except that pd6 and pd16 (ON medication) were low-pass filtered because the raw files were lost, so a sensitivity analysis excluding those two sessions is planned; (c) reference is BioSemi CMS/DRL; (d) per the maintainers, subject pd17 shows a persistent single-channel (P8) artefact; (e) no electrode coordinates beyond channel names; education was not collected.
- Suitability: small independent external test cohort; **not** suitable as a training set. The maintainers explicitly describe ML classification of PD vs HC on this dataset as problematic (fewer than 8 patients in any test split). This project therefore (i) uses ds002778 only as an external test set for models trained on ds007526 (no model is trained on it in the primary analysis), (ii) puts domain-shift diagnostics first, and (iii) will contact the maintainers before any manuscript is submitted.

## PPMI

- Source: https://www.ppmi-info.org/. Access (**verified from the PPMI "Access Data" page**): not an open download; requires signing the Data Use Agreement, an online application, and agreeing to the Publications Policy. Investigator-level eligibility; annual reporting obligations. Some assay data are sequestered.
- Participant counts, imaging inventory and licence terms: **not verified** (data not accessible without approval). Listed as a future validation opportunity.

## OASIS-3

- Source: https://www.oasis-brains.org/ (hosted on NITRC-IR). Per the OASIS site on 2026-11-08: 1,378 participants (755 cognitively normal, 622 at various stages of decline), 2,842 MR sessions, >2,157 raw PET scans, T1w/T2w/FLAIR/ASL/SWI/TOF/rBOLD/DTI, FreeSurfer segmentations for many sessions. These are the website's figures, **not verified at participant level**.
- Access: NITRC registration, OASIS staff review, data use agreement (non-commercial academic use; no re-identification or facial reconstruction; secure storage; acknowledgements; Avid pre-submission rule for AV45/AV1451 papers).
- Diagnostic labels, MMSE/CDR availability and longitudinal structure: **not verified** until the data dictionary is accessible.

## ADNI

- Source: https://adni.loni.usc.edu/. Access requires an ADNI application and a signed Data Use Agreement through LONI (data and biosamples use separate processes). Participant counts, diagnostic categories and licence terms: **not verified**.

## Alzheimer's Disease Data Initiative and other repositories

- ADDI discovery portal: **not investigated** in this session.
- PhysioNet, Zenodo, Figshare and further OpenNeuro searches for additional PD/AD datasets were **not completed** because those hosts were unreachable from the build sandbox. A literature-based search for further open datasets remains to be done.

## Proposed training / validation combinations

| Combination | Status |
|---|---|
| PD EEG: ds007526 → ds002778, resting state, features over the 31 shared scalp channels and 10-20 regions (reverse direction exploratory only, off by default) | Code implemented (`scripts/run_external_validation.py`); **not run** (signals unavailable). Main risks: different montages (65 vs 40 ch), sampling rates (250 vs 512 Hz), mains frequency (50 vs 60 Hz), amplifiers and references; ds002778 n=31. |
| PD: PPMI as additional external cohort | Planned; needs approval; PPMI has no resting EEG in the standard release (**not verified**), so likely clinical/imaging only. |
| AD: OASIS-3 → ADNI (and reverse) | Planned; needs approvals; label and acquisition harmonisation required first. |
