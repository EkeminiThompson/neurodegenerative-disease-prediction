#!/usr/bin/env python
"""Within-cohort PD vs HC experiments: clinical-only, EEG-only, clinical + EEG.

Requires features from scripts/extract_eeg_features.py (real recordings). One row per
participant is used (ds002778: OFF-medication session by default), grouped by
participant_id. Feature selection (SelectKBest) sits inside each training fold.

IMPORTANT: ds002778 has 31 participants and its maintainers advise against ML
classification on it; treat any ds002778-only result as exploratory with very wide CIs.
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from ndpred import SEED
from ndpred.data import bids
from ndpred.evaluation.cv import average_over_repeats, repeated_group_cv
from ndpred.evaluation.metrics import summarise_with_ci
from ndpred.models.baselines import CLASSIFIERS, make_classifier
from ndpred.utils.tracking import log_run, set_seed

CLINICAL = {"ds007526": ["age", "sex", "moca"], "ds002778": ["age", "sex", "mmse"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=sorted(CLINICAL), required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--features", required=True, help="CSV from extract_eeg_features.py")
    ap.add_argument("--session", default="off", help="ds002778 only: on|off")
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()
    set_seed(SEED)

    loader = bids.load_ds007526 if args.dataset == "ds007526" else bids.load_ds002778
    meta = loader(args.root)
    feat = pd.read_csv(args.features)
    if args.dataset == "ds002778":
        feat = feat[feat["session"].isin([args.session, "hc"])]
    df = meta.merge(feat, on="participant_id", how="inner")
    assert df["participant_id"].is_unique, "expected one row per participant"
    print(f"{args.dataset}: {len(df)} participants with EEG ({df['label'].sum()} PD)")

    eeg_cols = [c for c in df.columns if c.startswith(("core_", "reg_"))]
    sets = {"clinical": CLINICAL[args.dataset], "eeg_region": eeg_cols,
            "clinical+eeg": CLINICAL[args.dataset] + eeg_cols}
    rows = []
    for sname, cols in sets.items():
        k = None if sname == "clinical" else min(args.k, len(cols))
        for model in CLASSIFIERS:
            oof = repeated_group_cv(lambda m=model, kk=k: make_classifier(m, SEED, kk), df[cols],
                                    df["label"], df["participant_id"], 5, args.repeats, SEED)
            avg = average_over_repeats(oof)
            s = summarise_with_ci(avg["y"], avg["pred"], avg["group"], seed=SEED)
            cfg = {"dataset": args.dataset, "features": sname, "n_features": len(cols), "k": k,
                   "model": model, "session": args.session, "repeats": args.repeats}
            log_run(Path(args.out) / "results" / "runs.jsonl",
                    f"EEG/{args.dataset}/{sname}/{model}", cfg, s)
            rows.append({"dataset": args.dataset, "features": sname, "model": model, "n": s["n"],
                         "n_PD": s["n_pos"], "roc_auc": s["roc_auc"],
                         "roc_auc_lo": s["roc_auc_ci95"][0], "roc_auc_hi": s["roc_auc_ci95"][1],
                         "pr_auc": s["pr_auc"], "balanced_accuracy": s["balanced_accuracy"],
                         "sensitivity": s["sensitivity"], "specificity": s["specificity"],
                         "brier": s["brier"], "ece": s["ece"]})
            print(rows[-1])
    tdir = Path(args.out) / "tables"
    tdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(tdir / f"eeg_within_{args.dataset}.csv", index=False)
    (Path(args.out) / "results" / f"eeg_within_{args.dataset}.json").write_text(
        json.dumps(rows, indent=2, default=float))


if __name__ == "__main__":
    main()
