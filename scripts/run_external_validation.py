#!/usr/bin/env python
"""Cross-cohort PD vs HC external validation: ds007526 -> ds002778 (resting EEG).

Development cohort is used for ALL fitting; the external cohort is only predicted on.
Only features present in both cohorts are used: core_* (mean over the 31 scalp channels shared by both
montages) and region-level reg_*; channel-level features are excluded. Two conditions are
always reported side by side:
  raw          : features as extracted
  cohort-z     : each cohort z-scored on its own features (label-free, transductive)
Domain-shift diagnostics (standardized mean differences and a domain-classifier AUC)
quantify how separable the cohorts are before any disease labels are considered.

Usage: python scripts/run_external_validation.py \
  --a-features data/processed/ds007526_rest_eeg_features.csv --a-root data/raw/ds007526 \
  --b-features data/processed/ds002778_rest_eeg_features.csv --b-root data/raw/ds002778
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from ndpred import SEED
from ndpred.data import bids
from ndpred.evaluation.cv import average_over_repeats, repeated_group_cv
from ndpred.evaluation.external import (
    domain_classifier_auc,
    external_validate,
    standardized_mean_differences,
    zscore_within_cohort,
)
from ndpred.evaluation.metrics import summarise_with_ci
from ndpred.models.baselines import CLASSIFIERS, make_classifier
from ndpred.utils.tracking import log_run, set_seed


def load(root, feats_csv, loader, session=None):
    meta = loader(root)
    f = pd.read_csv(feats_csv)
    if session is not None:
        f = f[f["session"].isin([session, "hc"])]
    df = meta.merge(f, on="participant_id", how="inner")
    assert df["participant_id"].is_unique
    return df.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a-root", required=True)
    ap.add_argument("--a-features", required=True)
    ap.add_argument("--b-root", required=True)
    ap.add_argument("--b-features", required=True)
    ap.add_argument("--b-session", default="off")
    ap.add_argument("--k", type=int, default=15)
    ap.add_argument("--include-reverse", action="store_true",
                    help="EXPLORATORY: also train on ds002778 (15 PD). The ds002778 maintainers advise "
                         "against ML classification on this cohort; off by default.")
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()
    set_seed(SEED)
    A = load(args.a_root, args.a_features, bids.load_ds007526)
    B = load(args.b_root, args.b_features, bids.load_ds002778, args.b_session)
    shared = sorted(set(c for c in A.columns if c.startswith(("core_", "reg_")))
                    & set(c for c in B.columns if c.startswith(("core_", "reg_"))))
    print(f"A=ds007526 n={len(A)}, B=ds002778 n={len(B)}, shared features={len(shared)}")

    out = Path(args.out)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    diag = {"domain_classifier_auc": domain_classifier_auc(A[shared], B[shared], SEED),
            "top_standardized_mean_differences": standardized_mean_differences(
                A[shared], B[shared]).head(15).to_dict()}
    print("domain shift:", json.dumps(diag, indent=2))

    rows = []
    directions = [("ds007526", A, "ds002778", B)]
    if args.include_reverse:
        directions.append(("ds002778", B, "ds007526", A))
    for (dev_n, dev, ext_n, ext) in directions:
        for cond in ("raw", "cohort-z"):
            Xd, Xe = dev[shared], ext[shared]
            if cond == "cohort-z":
                Xd, Xe = zscore_within_cohort(Xd), zscore_within_cohort(Xe)
            k = min(args.k, len(shared))
            for model in CLASSIFIERS:
                est = make_classifier(model, SEED, k)
                ext_res = external_validate(est, Xd, dev["label"], Xe, ext["label"],
                                            ext["participant_id"], seed=SEED)
                oof = repeated_group_cv(lambda m=model, kk=k: make_classifier(m, SEED, kk), Xd,
                                        dev["label"], dev["participant_id"], 5, 10, SEED)
                avg = average_over_repeats(oof)
                internal = summarise_with_ci(avg["y"], avg["pred"], avg["group"], seed=SEED)
                row = {"develop": dev_n, "external": ext_n, "condition": cond, "model": model,
                       "n_dev": len(dev), "n_ext": len(ext),
                       "internal_auc": internal["roc_auc"], "external_auc": ext_res["roc_auc"],
                       "external_auc_lo": ext_res["roc_auc_ci95"][0],
                       "external_auc_hi": ext_res["roc_auc_ci95"][1],
                       "auc_drop": internal["roc_auc"] - ext_res["roc_auc"],
                       "external_pr_auc": ext_res["pr_auc"], "external_brier": ext_res["brier"],
                       "external_ece": ext_res["ece"],
                       "external_sensitivity": ext_res["sensitivity"],
                       "external_specificity": ext_res["specificity"]}
                log_run(out / "results" / "runs.jsonl", f"EXT/{dev_n}->{ext_n}/{cond}/{model}",
                        {"shared_features": len(shared), "k": k, **{x: row[x] for x in
                         ("develop", "external", "condition", "model")}}, row)
                rows.append(row)
                print(row)
    pd.DataFrame(rows).to_csv(out / "tables" / "external_validation_ds007526_ds002778.csv",
                              index=False)
    (out / "results" / "domain_shift_ds007526_ds002778.json").write_text(
        json.dumps(diag, indent=2, default=float))


if __name__ == "__main__":
    main()
