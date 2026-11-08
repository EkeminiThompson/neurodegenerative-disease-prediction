# Data dictionary (variables actually used)

## Harmonised participant table (`ndpred.data.bids`)

| Column | Meaning | Unit / coding | ds007526 source | ds002778 source |
|---|---|---|---|---|
| participant_id | BIDS subject ID | text | `participant_id` | `participant_id` |
| cohort | dataset ID | text | constant | constant |
| group | diagnostic group | HC / PD | `group` | prefix of `participant_id` (`sub-hc`, `sub-pd`) |
| label | binary target | HC=0, PD=1 | from `group` | from `group` |
| age | age at assessment | years | `age` | `age` |
| sex | sex | F=0, M=1 | `sex` | `gender` (f/m) |
| moca | Montreal Cognitive Assessment | points, 0-30 | `moca` | n/a |
| mmse | Mini-Mental State Examination | points, 0-30 | n/a | `MMSE` |
| naart | North American Adult Reading Test | points | n/a | `NAART` |
| updrs_iii | MDS-UPDRS part III (motor) | points | `updrs_part_iii` | per-session beh JSON (not in participants.tsv) |
| updrs_total | UPDRS total | points | `updrs_total` | beh JSON "Total UPDRS" |
| disease_duration | time since diagnosis | **ds007526: unit undocumented**; ds002778: years | `disease_duration` | `disease_duration` |
| ledd | levodopa equivalent daily dose | mg/day | `ledd` | not available |
| hoehn_yahr | Hoehn & Yahr stage | 1-5 | not available | beh JSON "H&Y", PD only |

Missing values (`n/a` upstream) stay missing. Nothing is inferred.

## Label-leaking variables (never used as classification features)

`updrs_part_iii`, `updrs_total`, `disease_duration`, `ledd`, `pigd_score`, `td_score`:
defined only for, or strongly diagnostic of, PD. They are used only as Level-2 targets or
predictors **within PD**.

## EEG features (`ndpred.features.eeg`)

Computed per 4 s window from the 1-45 Hz band-passed, average-referenced signal, then
the **median over windows** gives one value per channel per recording.

| Feature | Definition | Unit |
|---|---|---|
| abs_{delta,theta,alpha,beta,gamma} | Welch PSD integrated over 1-4, 4-8, 8-13, 13-30, 30-45 Hz | µV² |
| rel_{band} | abs_band / power in 1-45 Hz | ratio |
| spec_entropy | normalised Shannon entropy of the 1-45 Hz PSD | 0-1 |
| paf | frequency of the PSD maximum in 6-13 Hz | Hz |
| hjorth_activity / mobility / complexity | Hjorth parameters of the time series | µV², ratio, ratio |
| theta_beta_ratio, alpha_theta_ratio | ratios of absolute band powers | ratio |

Naming: `ch_<CHANNEL>_<feature>` (within-cohort only), `reg_<region>_<feature>` (mean of
channel medians across a 10-20 region), `global_<feature>` (mean over all channels).
Regions: frontal, central, temporal, parietal, occipital (`REGIONS_1020`).
