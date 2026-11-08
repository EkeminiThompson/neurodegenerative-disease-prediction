#!/usr/bin/env python
"""Fetch PUBLIC BIDS metadata (no signal files) for the open Parkinson's EEG cohorts.

Clones the OpenNeuro GitHub mirrors shallowly. The mirrors store EEG recordings as
git-annex objects, so this downloads participants.tsv, sidecars, events, channels and
READMEs only. Use scripts/download_eeg.py for the signals.

Usage: python scripts/fetch_metadata.py [--dest data/raw]
"""

import argparse
import subprocess
from pathlib import Path

DATASETS = ["ds007526", "ds002778"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default="data/raw")
    args = ap.parse_args()
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    for ds in DATASETS:
        target = dest / ds
        if target.exists():
            print(f"{ds}: already present at {target}, leaving untouched")
            continue
        subprocess.run(
            ["git", "clone", "--depth", "1", f"https://github.com/OpenNeuroDatasets/{ds}.git",
             str(target)], check=True)
        sha = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True,
                             capture_output=True, text=True).stdout.strip()
        print(f"{ds}: cloned metadata at mirror commit {sha}")


if __name__ == "__main__":
    main()
