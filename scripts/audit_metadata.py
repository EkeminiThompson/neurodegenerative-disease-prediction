#!/usr/bin/env python
"""Compute verifiable dataset-audit numbers from local BIDS metadata.

Writes data/manifests/<dataset>.json (counts, non-missing clinical variables, file
checksums). Every number in docs/dataset_audit.md must be reproducible with this script.
"""

import argparse
import glob
import json
import subprocess
from pathlib import Path

from ndpred.data import bids
from ndpred.data.manifest import sha256, write_manifest

LOADERS = {"ds007526": bids.load_ds007526, "ds002778": bids.load_ds002778}


def audit(root: Path, name: str) -> dict:
    df = LOADERS[name](root)
    rec = {"dataset": name, "n_participants": int(len(df)),
           "group_counts": df["group"].value_counts().to_dict(),
           "non_missing": {c: int(df[c].notna().sum()) for c in df.columns}}
    sidecars = glob.glob(str(root / "sub-*/**/*_eeg.json"), recursive=True)
    tasks: dict[str, int] = {}
    for f in sidecars:
        t = next((x for x in Path(f).name.split("_") if x.startswith("task-")), "task-?")
        tasks[t] = tasks.get(t, 0) + 1
    rec["eeg_recordings_by_task"] = tasks
    rec["n_eeg_recordings"] = sum(tasks.values())
    if sidecars:
        j = json.loads(Path(sidecars[0]).read_text())
        rec["example_sidecar"] = {k: j.get(k) for k in
                                  ("SamplingFrequency", "EEGChannelCount", "PowerLineFrequency",
                                   "Manufacturer")}
    rec["participants_tsv_sha256"] = sha256(root / "participants.tsv")
    git = root / ".git"
    if git.exists():
        rec["mirror_commit"] = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                                              capture_output=True, text=True).stdout.strip()
    if name == "ds002778":
        s = bids.load_ds002778_sessions(root)
        rec["pd_sessions"] = s["session"].value_counts().to_dict()
        rec["hoehn_yahr_non_missing_sessions"] = int(s["hoehn_yahr"].notna().sum())
        rec["hoehn_yahr_values"] = s["hoehn_yahr"].value_counts().sort_index().to_dict()
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/manifests")
    args = ap.parse_args()
    Path(args.out).mkdir(parents=True, exist_ok=True)
    for name in LOADERS:
        root = Path(args.raw) / name
        if not (root / "participants.tsv").exists():
            print(f"{name}: not found under {root}; run scripts/fetch_metadata.py")
            continue
        rec = audit(root, name)
        write_manifest(Path(args.out) / f"{name}.json", rec)
        print(json.dumps(rec, indent=2, default=str))


if __name__ == "__main__":
    main()
