# Data

No participant-level data is stored in git. Folders `raw/`, `interim/`, `processed/`
and `external/` are empty placeholders (`.gitkeep`) and are git-ignored.

`manifests/` holds provenance for the open datasets: counts computed by
`scripts/audit_metadata.py`, the SHA-256 of each `participants.tsv`, and the mirror commit.

## Acquisition checklist

| Dataset | How | Approval needed? | Status |
|---|---|---|---|
| ds007526 metadata | `python scripts/fetch_metadata.py` | No (CC0) | Done |
| ds007526 EEG | `python scripts/download_eeg.py --dataset ds007526` (needs OpenNeuro access) | No (CC0) | **To do on a machine with network access** |
| ds002778 metadata | `python scripts/fetch_metadata.py` | No (CC0) | Done |
| ds002778 EEG | `python scripts/download_eeg.py --dataset ds002778` | No (CC0), but email maintainers before publishing | **To do** |
| PPMI | https://www.ppmi-info.org/access-data-specimens/download-data | Yes: DUA + application | Not requested |
| OASIS-3 | https://www.oasis-brains.org/ (NITRC-IR) | Yes: registration + DUA | Not requested |
| ADNI | https://adni.loni.usc.edu/data-samples/adni-data/ | Yes: application + DUA | Not requested |

Alternative to `openneuro-py`: `datalad install https://github.com/OpenNeuroDatasets/ds007526`
then `datalad get sub-*/eeg/*task-rest*`.

Verify integrity after download by re-running `python scripts/audit_metadata.py` and comparing
with `manifests/*.json`.
