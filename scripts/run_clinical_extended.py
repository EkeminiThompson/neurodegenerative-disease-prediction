#!/usr/bin/env python
"""Extended real-data analyses on ds007526 clinical metadata (no EEG signals needed).

A1  Paired participant-level bootstrap comparison of models (age+sex+MoCA, PD vs HC):
    difference in ROC-AUC with 95% CI for every model pair, plus Holm-adjusted flags.
A2  Calibration: reliability curves and ECE/Brier for each model; platt-style recalibration
    is NOT applied (reported as-is).
A3  Age-matched sensitivity analysis: every HC is matched 1:1 to the PD participant closest in
    age (caliper 3 years, without replacement). Age alone should then be ~chance; the
    remaining signal of MoCA/sex is the age-independent component.
A4  Subgroup performance by sex (out-of-fold predictions of A1, evaluated within sex).
A5  Nested CV: inner grouped 3-fold grid search (logistic C; RF min_samples_leaf) inside each
    outer fold, so tuning never sees outer-test participants.

All CV is stratified GROUP k-fold by participant_id; preprocessing is fitted inside folds.
"""

import argparse
import itertools
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline

from ndpred import SEED
from ndpred.data import bids
from ndpred.evaluation.cv import assert_no_group_overlap, average_over_repeats, repeated_group_cv
from ndpred.evaluation.metrics import binary_metrics, reliability_table, summarise_with_ci
from ndpred.models.baselines import make_classifier
from ndpred.utils.tracking import log_run, set_seed

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MODELS = ["logreg", "rf", "svm", "xgboost", "lightgbm"]
COLS = ["age", "sex", "moca"]


def paired_bootstrap(preds: dict[str, pd.DataFrame], n_boot=2000, seed=0):
    """preds[model] = DataFrame(row, group, y, pred) aligned on row. Resample participants."""
    base = preds[MODELS[0]].sort_values("row").reset_index(drop=True)
    y, g = base["y"].values, base["group"].values
    P = {m: preds[m].sort_values("row")["pred"].values for m in MODELS}
    ug = np.unique(g)
    idx_of = {u: np.where(g == u)[0] for u in ug}
    rng = np.random.default_rng(seed)
    from sklearn.metrics import roc_auc_score

    diffs = {pair: [] for pair in itertools.combinations(MODELS, 2)}
    for _ in range(n_boot):
        pick = rng.choice(ug, len(ug), replace=True)
        i = np.concatenate([idx_of[u] for u in pick])
        if len(np.unique(y[i])) < 2:
            continue
        auc = {m: roc_auc_score(y[i], P[m][i]) for m in MODELS}
        for a, b in diffs:
            diffs[(a, b)].append(auc[a] - auc[b])
    rows = []
    for (a, b), d in diffs.items():
        d = np.asarray(d)
        lo, hi = np.percentile(d, [2.5, 97.5])
        p = 2 * min((d <= 0).mean(), (d >= 0).mean())
        rows.append({"model_a": a, "model_b": b, "auc_diff_mean": d.mean(), "ci_lo": lo,
                     "ci_hi": hi, "p_boot": min(p, 1.0)})
    df = pd.DataFrame(rows).sort_values("p_boot").reset_index(drop=True)
    m = len(df)
    df["p_holm"] = [min(1.0, (m - i) * p) for i, p in enumerate(df["p_boot"])]
    df["p_holm"] = np.maximum.accumulate(df["p_holm"].values)
    df["significant_holm_0.05"] = df["p_holm"] < 0.05
    return df


def age_match(df: pd.DataFrame, caliper=3.0):
    hc = df[df["label"] == 0].sort_values("age")
    pdf = df[df["label"] == 1].copy()
    used, keep = set(), []
    for _, r in hc.iterrows():
        cand = pdf[~pdf.index.isin(used)].copy()
        cand["d"] = (cand["age"] - r["age"]).abs()
        cand = cand[cand["d"] <= caliper].sort_values("d")
        if len(cand):
            used.add(cand.index[0])
            keep += [r.name, cand.index[0]]
    return df.loc[keep].reset_index(drop=True)


def nested_cv(df, model, grid, n_splits=5, repeats=5, seed=0):
    X, y, g = df[COLS].reset_index(drop=True), df["label"].values, df["participant_id"].values
    recs = []
    for r in range(repeats):
        outer = StratifiedGroupKFold(n_splits, shuffle=True, random_state=seed + r)
        for tr, te in outer.split(X, y, g):
            assert_no_group_overlap(g[tr], g[te])
            inner = StratifiedGroupKFold(3, shuffle=True, random_state=seed + 100 + r)
            gs = GridSearchCV(make_classifier(model, seed), grid, scoring="roc_auc",
                              cv=list(inner.split(X.iloc[tr], y[tr], g[tr])), n_jobs=1)
            gs.fit(X.iloc[tr], y[tr])
            recs.append(pd.DataFrame({"repeat": r, "row": te, "group": g[te], "y": y[te],
                                      "pred": gs.predict_proba(X.iloc[te])[:, 1]}))
    return pd.concat(recs, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/raw/ds007526")
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()
    set_seed(SEED)
    out = Path(args.out)
    for d in ("tables", "results", "figures"):
        (out / d).mkdir(parents=True, exist_ok=True)
    df = bids.load_ds007526(args.root).dropna(subset=COLS).reset_index(drop=True)
    print(f"analysis set: n={len(df)}, PD={int(df['label'].sum())}, HC={int((df['label'] == 0).sum())}")
    summary: dict = {"n": len(df), "n_pd": int(df["label"].sum())}

    # ---- A1/A2/A4 predictions
    preds = {}
    for m in MODELS:
        oof = repeated_group_cv(lambda mm=m: make_classifier(mm, SEED), df[COLS], df["label"],
                                df["participant_id"], 5, args.repeats, SEED)
        preds[m] = average_over_repeats(oof)
        print("fitted", m, flush=True)

    cmp_df = paired_bootstrap(preds, seed=SEED)
    cmp_df.to_csv(out / "tables" / "a1_paired_model_comparison.csv", index=False)
    print(cmp_df.round(3).to_string())

    # ---- A2 calibration
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    cal_rows = []
    for m in MODELS:
        tab = pd.DataFrame(reliability_table(preds[m]["y"], preds[m]["pred"], 5))
        ax.plot(tab["mean_predicted"], tab["observed_rate"], marker="o", label=m)
        s = binary_metrics(preds[m]["y"], preds[m]["pred"])
        cal_rows.append({"model": m, "brier": s["brier"], "ece": s["ece"]})
    ax.set_xlabel("Mean predicted P(PD)")
    ax.set_ylabel("Observed PD fraction")
    ax.set_title("A2: calibration, age+sex+MoCA (ds007526, n=%d)" % len(df), fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "figures" / "a2_calibration.png", dpi=200)
    pd.DataFrame(cal_rows).to_csv(out / "tables" / "a2_calibration.csv", index=False)

    # ---- A4 subgroup by sex
    sg = []
    meta = df[["participant_id", "sex"]].rename(columns={"participant_id": "group"})
    for m in MODELS:
        merged = preds[m].merge(meta, on="group")
        for sex, name in ((0, "female"), (1, "male")):
            sub = merged[merged["sex"] == sex]
            if sub["y"].nunique() < 2 or (sub["y"] == 0).sum() < 5:
                continue
            s = summarise_with_ci(sub["y"], sub["pred"], sub["group"], n_boot=1000, seed=SEED)
            sg.append({"model": m, "subgroup": name, "n": s["n"], "n_HC": int((sub["y"] == 0).sum()),
                       "roc_auc": s["roc_auc"], "ci_lo": s["roc_auc_ci95"][0],
                       "ci_hi": s["roc_auc_ci95"][1]})
    pd.DataFrame(sg).to_csv(out / "tables" / "a4_subgroup_sex.csv", index=False)
    print(pd.DataFrame(sg).round(3).to_string())

    # ---- A3 age-matched sensitivity
    matched = age_match(df)
    summary["age_matched"] = {
        "n": len(matched), "n_pd": int(matched["label"].sum()),
        "mean_age_pd": float(matched.loc[matched.label == 1, "age"].mean()),
        "mean_age_hc": float(matched.loc[matched.label == 0, "age"].mean())}
    print("matched:", summary["age_matched"])
    mrows = []
    for fname, cols in {"age_only": ["age"], "sex_moca": ["sex", "moca"],
                        "age_sex_moca": ["age", "sex", "moca"]}.items():
        for m in ("logreg", "rf"):
            oof = repeated_group_cv(lambda mm=m: make_classifier(mm, SEED), matched[cols],
                                    matched["label"], matched["participant_id"], 5,
                                    args.repeats, SEED)
            avg = average_over_repeats(oof)
            s = summarise_with_ci(avg["y"], avg["pred"], avg["group"], seed=SEED)
            mrows.append({"features": fname, "model": m, "n": s["n"], "n_PD": s["n_pos"],
                          "roc_auc": s["roc_auc"], "ci_lo": s["roc_auc_ci95"][0],
                          "ci_hi": s["roc_auc_ci95"][1], "brier": s["brier"]})
            print(mrows[-1], flush=True)
    pd.DataFrame(mrows).to_csv(out / "tables" / "a3_age_matched_sensitivity.csv", index=False)

    # ---- A5 nested CV
    nrows = []
    for m, grid in {"logreg": {"clf__C": [0.01, 0.1, 1.0, 10.0]},
                    "rf": {"clf__min_samples_leaf": [1, 3, 5], "clf__max_depth": [2, 4, None]}}.items():
        oof = nested_cv(df, m, grid, repeats=3, seed=SEED)
        avg = average_over_repeats(oof)
        s = summarise_with_ci(avg["y"], avg["pred"], avg["group"], seed=SEED)
        nrows.append({"model": m, "tuning": "nested inner 3-fold grouped", "n": s["n"],
                      "roc_auc": s["roc_auc"], "ci_lo": s["roc_auc_ci95"][0],
                      "ci_hi": s["roc_auc_ci95"][1], "brier": s["brier"], "ece": s["ece"]})
        print(nrows[-1], flush=True)
    pd.DataFrame(nrows).to_csv(out / "tables" / "a5_nested_cv.csv", index=False)

    log_run(out / "results" / "runs.jsonl", "EXT-clinical/a1-a5",
            {"dataset": "ds007526 v1.0.2", "features": COLS, "repeats": args.repeats, "seed": SEED},
            summary)
    (out / "results" / "clinical_extended_summary.json").write_text(
        json.dumps(summary, indent=2, default=float))
    assert isinstance(Pipeline, type)
    print("done")


if __name__ == "__main__":
    main()
