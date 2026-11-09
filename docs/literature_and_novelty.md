# Literature check and novelty assessment

Scope: a targeted search in November 2026, not a systematic review. Only statements read in the cited sources' text are recorded; sources I could not open are marked "not read".

## What the sources say

| Source | Verified content |
|---|---|
| [Generalizable EEG classification of PD (medRxiv 2022.08.30.22279401)](https://www.medrxiv.org/content/10.1101/2022.08.30.22279401v1.full) | Trained on UNM (N=54, 27 PD), frozen and tested on Iowa (N=28, 14 PD); subject-level accuracy about 77% internal (leave-one-subject-out) and 84% external. Reports that epoch-level CV with leakage inflated metrics by about 20% or more. The text read does not mention age or sex. |
| [Rasmussen et al., arXiv 2604.23933](https://arxiv.org/pdf/2604.23933) | Five PD EEG cohorts (285 participants), all directional train-test configurations, nested CV with inner-loop channel selection, patient-level splits. Transfer is asymmetric; site identity is recoverable from embeddings (over 90% accuracy). Controls are described as age- and sex-matched in some cohorts; no explicit age or sex adjustment is described. |
| [TransformEEG, arXiv 2507.07622](https://arxiv.org/pdf/2507.07622) | Pools four OpenNeuro datasets including ds002778 (290 subjects); nested leave-N-subjects-out; balanced accuracy median 78.45%. No leave-one-dataset-out test described; sex not reported and age/sex not analysed as confounds; one healthy-only dataset has mean age about 20. |
| [Channel-selected stratified nested CV, arXiv 2601.05276](https://arxiv.org/abs/2601.05276) | Iowa, UNM and San Diego combined; StratifiedGroupKFold by patient; accuracy .985 without patient stratification versus .806 with it. Age and sex handling not described. |
| Brookshire et al., data leakage in translational EEG deep learning (PMC11099244) | Not read (page not fetchable here). Cited only by title. |
| Bias investigation in AI systems for early PD detection (PMC8774851) | Not read (access blocked). Cited only by title. |

## Assessment

- **Not novel:** leakage-safe participant-level CV, nested CV, cross-cohort transfer and demonstrating leakage inflation have all been reported for PD EEG. This project does not claim them.
- **Possibly a gap (within what I read):** none of the four papers read describes an explicit age-matched sensitivity analysis, and age/sex handling is absent or limited to the original cohort descriptions. Paper 1's age-matched result on ds007526 (clinical metadata falls to chance at n=54) fits that gap, but it is on clinical metadata, not EEG, and a systematic search has not been done, so absence in four papers is not proof of absence in the literature.
- **Cohort overlap:** ds002778 is already used in at least two of these studies. The dual-cohort metadata audit (Paper 2) is therefore a documentation contribution; ds007526 appears less used, but that was not verified.
- **Top-tier novelty is not established.** It would need real EEG results on ds007526 and ds002778 with age-matched and independent-cohort analyses, which have not been run.

## Before any novelty claim

Run a systematic search (PubMed, Scopus, medRxiv, arXiv) for "age-matched" and "confound" in PD EEG classification, and read the two unread sources.
