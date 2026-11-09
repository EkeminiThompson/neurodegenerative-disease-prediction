#!/usr/bin/env python
"""Descriptive longitudinal summary of ds007526 follow-up data (sourcedata/clinical_data).

Real data only; DESCRIPTIVE, not predictive. Follow-up values (n=39 PD) are compared with the
baseline values in participants.tsv. Medication state at either assessment is not documented, so
change scores are confounded by ON/OFF state and regression to the mean; no progression claim is
made. Also reports how many item-level UPDRS rows (full_UPDRS_data.tsv) map to participants.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def boot_ci(x, n=5000, seed=0):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    rng = np.random.default_rng(seed)
    means = [rng.choice(x, len(x), replace=True).mean() for _ in range(n)]
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/raw/ds007526")
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()
    root = Path(args.root)
    p = pd.read_csv(root / "participants.tsv", sep="\t", na_values=["n/a"])
    L = pd.read_csv(root / "sourcedata/clinical_data/longitudinal_clinical_data.tsv", sep="\t")
    U = pd.read_csv(root / "sourcedata/clinical_data/full_UPDRS_data.tsv", sep="\t")
    m = L.merge(p, on="subject_id", how="inner", suffixes=("_fu", "_bl"))
    m["interval_years"] = (pd.to_datetime(m["followup_date"]) -
                           pd.to_datetime(m["eeg_date"])).dt.days / 365.25
    rows = [{"variable": "interval_years", "n": int(m["interval_years"].notna().sum()),
             "baseline_mean": np.nan, "followup_mean": np.nan,
             "mean_change": float(m["interval_years"].mean()), "ci_lo": np.nan, "ci_hi": np.nan,
             "min": float(m["interval_years"].min()), "max": float(m["interval_years"].max())}]
    for v in ("updrs_part_iii", "updrs_total", "moca", "ledd"):
        d = (m[f"{v}_fu"] - m[f"{v}_bl"]).dropna()
        lo, hi = boot_ci(d)
        base = float(m.loc[d.index, f"{v}_bl"].mean())
        rows.append({"variable": v, "n": int(len(d)), "baseline_mean": base,
                     "followup_mean": float(m.loc[d.index, f"{v}_fu"].mean()),
                     "mean_change": float(d.mean()), "ci_lo": lo, "ci_hi": hi,
                     "min": float(d.min()), "max": float(d.max())})
    tab = pd.DataFrame(rows)
    out = Path(args.out)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    tab.to_csv(out / "tables" / "longitudinal_descriptives_ds007526.csv", index=False)
    info = {"followup_rows": int(len(L)), "matched_to_participants": int(len(m)),
            "all_followup_are_PD": bool((m["group"] == "PD").all()),
            "item_level_updrs_rows": int(len(U)),
            "item_level_updrs_matched": int(U["Subject"].isin(p["subject_id"]).sum()),
            "item_level_has_hoehn_yahr_column": any("h&y" in c.lower() or "hoehn" in c.lower()
                                                    for c in U.columns)}
    (out / "results" / "longitudinal_info_ds007526.json").write_text(json.dumps(info, indent=2))
    print(tab.round(2).to_string(index=False))
    print(info)


if __name__ == "__main__":
    main()
