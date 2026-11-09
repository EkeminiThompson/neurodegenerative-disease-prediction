#!/usr/bin/env python
"""Extract participant-level EEG features from downloaded BIDS recordings.

Output: data/processed/<dataset>_<task>_eeg_features.csv, ONE ROW PER RECORDING
(participant_id, session) so that downstream splits can group by participant_id.
Recordings failing QC (too few clean windows) are listed in a sidecar CSV and dropped,
never imputed.

Usage: python scripts/extract_eeg_features.py --dataset ds007526 --root data/raw/ds007526
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from ndpred.features.eeg import CORE_CHANNELS, REGIONS_1020, participant_features
from ndpred.preprocessing.eeg import EEGConfig, preprocess, read_raw, usable


def recordings(dataset: str, root: Path, task: str):
    pattern = "sub-*/eeg/*_eeg.set" if dataset == "ds007526" else "sub-*/ses-*/eeg/*_eeg.bdf"
    for f in sorted(root.glob(pattern)):
        if f"task-{task}" not in f.name:
            continue
        parts = f.name.split("_")
        sub = parts[0]
        ses = next((p.replace("ses-", "") for p in parts if p.startswith("ses-")), "n/a")
        yield sub, ses, f


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["ds007526", "ds002778"], required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--task", default="rest")
    ap.add_argument("--out", default="data/processed")
    args = ap.parse_args()
    cfg = EEGConfig()
    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, dropped = [], []
    for sub, ses, f in recordings(args.dataset, root, args.task):
        if not f.exists():  # annexed file whose content was never downloaded
            dropped.append({"participant_id": sub, "session": ses, "reason": "file_not_downloaded"})
            continue
        side = f.with_suffix(".json")
        mains = json.loads(side.read_text()).get("PowerLineFrequency") if side.exists() else None
        try:
            win, names, qc = preprocess(read_raw(f), cfg, mains_hz=mains)
        except Exception as exc:  # record, don't hide
            dropped.append({"participant_id": sub, "session": ses, "reason": f"error: {exc}"})
            continue
        if not usable(qc, cfg):
            dropped.append({"participant_id": sub, "session": ses, "reason": "too_few_clean_windows",
                            **qc})
            continue
        feats = participant_features(win, cfg.sfreq, names, REGIONS_1020, CORE_CHANNELS)
        rows.append({"participant_id": sub, "session": ses, **qc, **feats})
        print(f"{sub} {ses}: {qc['n_windows_kept']}/{qc['n_windows_total']} windows")
    tag = f"{args.dataset}_{args.task}"
    pd.DataFrame(rows).to_csv(out / f"{tag}_eeg_features.csv", index=False)
    pd.DataFrame(dropped).to_csv(out / f"{tag}_eeg_dropped.csv", index=False)
    print(f"kept {len(rows)} recordings, dropped {len(dropped)}")


if __name__ == "__main__":
    main()
