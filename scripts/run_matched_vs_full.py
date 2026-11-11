#!/usr/bin/env python
"""Like-for-like full-cohort vs age-matched comparison on ds007526 (metadata only).

(1) Full-cohort AUC for every feature set that was evaluated in the age-matched subset
    (age, sex+MoCA, age+sex+MoCA), same complete-case sample (n=140), same CV protocol.
(2) A formal paired test of the difference AUC(full) - AUC(matched). The matched subset is
    nested in the full cohort, so participants are resampled once from the full cohort and
    both AUCs are computed on the same resample (matched-subset members that are drawn).
    Two contrasts are reported:
      D1 = AUC(full-cohort OOF) - AUC(matched-subset CV)            [separately trained]
      D2 = AUC(full-cohort OOF, all) - AUC(full-cohort OOF, matched members only)
           [same model, same predictions; isolates the effect of the sample composition]
    Two-sided percentile bootstrap p-value (2 x min tail). Exploratory.
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from ndpred import SEED
from ndpred.data import bids
from ndpred.evaluation.cv import average_over_repeats, repeated_group_cv
from ndpred.models.baselines import make_classifier
from ndpred.utils.tracking import log_run, set_seed

spec = importlib.util.spec_from_file_location("ext", Path(__file__).parent / "run_clinical_extended.py")
ext = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ext)

FEATS = {"age_only": ["age"], "sex_moca": ["sex", "moca"], "age_sex_moca": ["age", "sex", "moca"]}


def oof_auc(df, cols, model, repeats):
    oof = repeated_group_cv(lambda: make_classifier(model, SEED), df[cols], df["label"],
                            df["participant_id"], 5, repeats, SEED)
    avg = average_over_repeats(oof)
    out = df.reset_index(drop=True).copy()
    out["pred"] = avg.sort_values("row")["pred"].to_numpy()
    return out


def auc(y, p):
    return roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/raw/ds007526")
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--boot", type=int, default=5000)
    args = ap.parse_args()
    set_seed(SEED)
    df = bids.load_ds007526(args.root).dropna(subset=["age", "sex", "moca"]).reset_index(drop=True)
    matched_ids = set(ext.age_match(df)["participant_id"])
    df["in_matched"] = df["participant_id"].isin(matched_ids)
    matched = df[df["in_matched"]].reset_index(drop=True)
    print(f"full n={len(df)} (PD {int(df.label.sum())}); matched n={len(matched)}")
    ids = df["participant_id"].to_numpy()
    rng = np.random.default_rng(SEED)
    boots = rng.integers(0, len(df), size=(args.boot, len(df)))  # participants = rows here (one row each)
    rows = []
    for fname, cols in FEATS.items():
        for model in ("logreg", "rf"):
            full = oof_auc(df, cols, model, args.repeats)
            mat = oof_auc(matched, cols, model, args.repeats)
            p_full = dict(zip(full["participant_id"], full["pred"]))
            p_mat = dict(zip(mat["participant_id"], mat["pred"]))
            y = df["label"].to_numpy()
            pf = np.array([p_full[i] for i in ids])
            pm = np.array([p_mat.get(i, np.nan) for i in ids])
            inm = df["in_matched"].to_numpy()
            d1, d2 = [], []
            for b in boots:
                yb, pfb, pmb, mb = y[b], pf[b], pm[b], inm[b]
                if len(np.unique(yb)) < 2 or len(np.unique(yb[mb])) < 2:
                    continue
                af, am, asub = auc(yb, pfb), auc(yb[mb], pmb[mb]), auc(yb[mb], pfb[mb])
                d1.append(af - am)
                d2.append(af - asub)
            def ci(x):
                return [float(v) for v in np.percentile(x, [2.5, 97.5])]
            def pv(x):
                x = np.asarray(x)
                return float(min(1.0, 2 * min((x <= 0).mean(), (x >= 0).mean())))
            rows.append({
                "features": fname, "model": model, "n_full": len(df), "n_matched": len(matched),
                "auc_full": auc(y, pf), "auc_matched_cv": auc(matched["label"], mat["pred"]),
                "auc_full_model_on_matched": auc(y[inm], pf[inm]),
                "d1_full_minus_matched": auc(y, pf) - auc(matched["label"], mat["pred"]),
                "d1_ci_lo": ci(d1)[0], "d1_ci_hi": ci(d1)[1], "d1_p": pv(d1),
                "d2_full_minus_submodel": auc(y, pf) - auc(y[inm], pf[inm]),
                "d2_ci_lo": ci(d2)[0], "d2_ci_hi": ci(d2)[1], "d2_p": pv(d2),
                "n_valid_boot": len(d1)})
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    res = pd.DataFrame(rows)
    Path("reports/tables").mkdir(parents=True, exist_ok=True)
    res.to_csv("reports/tables/x2_full_vs_matched.csv", index=False)
    log_run("reports/results/runs.jsonl", "X2_full_vs_matched",
            {"repeats": args.repeats, "boot": args.boot, "seed": SEED, "n_full": len(df),
             "n_matched": len(matched)}, {"rows": rows})


if __name__ == "__main__":
    main()
