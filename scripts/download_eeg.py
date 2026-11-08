#!/usr/bin/env python
"""Download the EEG signal files of the open (CC0) cohorts with openneuro-py.

Requires outbound access to OpenNeuro (not available in every sandbox). Only the
resting-state task is fetched by default; pass --include-walk for ds007526 walking EEG.

Usage:
    python scripts/download_eeg.py --dataset ds007526 --dest data/raw
    python scripts/download_eeg.py --dataset ds002778 --dest data/raw
"""

import argparse
from pathlib import Path

VERSIONS = {"ds007526": "1.0.2", "ds002778": "1.0.5"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=sorted(VERSIONS), required=True)
    ap.add_argument("--dest", default="data/raw")
    ap.add_argument("--include-walk", action="store_true")
    args = ap.parse_args()

    import openneuro

    include = ["participants.tsv", "dataset_description.json", "README*", "CHANGES"]
    include += ["sub-*/**/*task-rest*", "sub-*/*scans.tsv", "sub-*/**/*beh*"]
    if args.include_walk and args.dataset == "ds007526":
        include.append("sub-*/**/*task-walk*")
    target = Path(args.dest) / args.dataset
    openneuro.download(dataset=args.dataset, tag=VERSIONS[args.dataset], target_dir=target,
                       include=include)
    print(f"Downloaded {args.dataset} v{VERSIONS[args.dataset]} to {target}")


if __name__ == "__main__":
    main()
