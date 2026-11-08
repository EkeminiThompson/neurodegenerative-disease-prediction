#!/usr/bin/env python
"""Real-data clinical-only baselines on ds007526 metadata (no EEG signals needed).

E0  Level 1: PD vs HC from age + sex + MoCA only. UPDRS, LEDD and disease duration are
    EXCLUDED on purpose: they are defined only for (or are diagnostic of) PD, so including
    them would leak the label. An age-only model is run alongside to expose the known
    age imbalance between groups (HC are younger), i.e. how much of the signal is
    demographic confounding.
E1  Level 2: UPDRS part III severity within PD, regression from age, sex, MoCA,
    disease duration, LEDD. Compared against a predict-the-training-mean baseline.

All numbers come from repeated, participant-grouped, stratified 5-fold CV.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import make_pipeline

from ndpred import SEED
from ndpred.data import bids
from ndpred.evaluation.cv import average_over_repeats, repeated_group_cv
from ndpred.evaluation.metrics import ordinal_metrics, summarise_with_ci
from ndpred.models.baselines import CLASSIFIERS, make_classifier, make_regressor
from ndpred.utils.tracking import log_run, set_seed


def bootstrap_reg(y, p, groups, n_boot=2000, seed=0):
    rng = np.random.default_rng(seed)
    ug = np.unique(groups)
    idx_of = {g: np.where(groups == g)[0] for g in ug}
    maes, rhos = [], []
    for _ in range(n_boot):
        pick = rng.choice(ug, len(ug), replace=True)
        i = np.concatenate([idx_of[g] for g in pick])
        m = ordinal_metrics(y[i], p[i])
        maes.append(m["mae"])
        rhos.append(m["spearman_rho"])
    f = lambda a: [float(x) for x in np.nanpercentile(a, [2.5, 97.5])]  # noqa: E731
    return {"mae_ci95": f(maes), "spearman_ci95": f(rhos)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/raw/ds007526")
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()
    set_seed(SEED)
    out = Path(args.out)
    (out / "results").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(parents=True, exist_ok=True)

    df = bids.load_ds007526(args.root)
    cfg_base = {"dataset": "ds007526 v1.0.2", "split": "StratifiedGroupKFold(5) x"
                f"{args.repeats} repeats, groups=participant_id", "seed": SEED}

    # ---- E0: PD vs HC, clinical-only -------------------------------------------------
    feats = {"age_only": ["age"], "age_sex_moca": ["age", "sex", "moca"]}
    rows, results = [], {}
    for fname, cols in feats.items():
        for model in CLASSIFIERS:
            oof = repeated_group_cv(lambda m=model: make_classifier(m, SEED), df[cols],
                                    df["label"], df["participant_id"], 5, args.repeats, SEED)
            avg = average_over_repeats(oof)
            s = summarise_with_ci(avg["y"], avg["pred"], avg["group"], seed=SEED)
            per_rep = [
                float(__import__("sklearn.metrics", fromlist=["x"]).roc_auc_score(g["y"], g["pred"]))
                for _, g in oof.groupby("repeat")]
            results[f"E0/{fname}/{model}"] = {**{k: v for k, v in s.items()},
                                              "auc_per_repeat_mean": float(np.mean(per_rep)),
                                              "auc_per_repeat_sd": float(np.std(per_rep))}
            log_run(out / "results" / "runs.jsonl", f"E0/{fname}/{model}",
                    {**cfg_base, "features": cols, "model": model}, results[f"E0/{fname}/{model}"])
            rows.append({"experiment": "E0 PD vs HC", "features": fname, "model": model,
                         "n": s["n"], "n_PD": s["n_pos"],
                         "ROC-AUC": f"{s['roc_auc']:.3f} ({s['roc_auc_ci95'][0]:.3f}-{s['roc_auc_ci95'][1]:.3f})",  # noqa: E501
                         "PR-AUC": f"{s['pr_auc']:.3f} ({s['pr_auc_ci95'][0]:.3f}-{s['pr_auc_ci95'][1]:.3f})",
                         "Bal.Acc": f"{s['balanced_accuracy']:.3f}",
                         "Sens": f"{s['sensitivity']:.3f}", "Spec": f"{s['specificity']:.3f}",
                         "Brier": f"{s['brier']:.3f}", "ECE": f"{s['ece']:.3f}"})
            print(rows[-1])
    pd.DataFrame(rows).to_csv(out / "tables" / "e0_clinical_pd_vs_hc.csv", index=False)

    # ---- E1: UPDRS-III severity within PD ------------------------------------------
    pdf = df[(df["label"] == 1) & df["updrs_iii"].notna()].reset_index(drop=True)
    cols = ["age", "sex", "moca", "disease_duration", "ledd"]
    sev_rows = []
    for name, factory in {
        "mean_baseline": lambda: make_pipeline(DummyRegressor(strategy="mean")),
        "ridge": lambda: make_regressor("ridge", SEED),
        "rf_regressor": lambda: make_regressor("rf", SEED),
    }.items():
        oof = repeated_group_cv(factory, pdf[cols], pdf["updrs_iii"], pdf["participant_id"], 5,
                                args.repeats, SEED, regression=True)
        avg = average_over_repeats(oof)
        m = ordinal_metrics(avg["y"].values, avg["pred"].values)
        ci = bootstrap_reg(avg["y"].values, avg["pred"].values, avg["group"].values, seed=SEED)
        results[f"E1/{name}"] = {**m, **ci}
        log_run(out / "results" / "runs.jsonl", f"E1/{name}",
                {**cfg_base, "features": cols, "model": name, "target": "updrs_part_iii"},
                results[f"E1/{name}"])
        rho_txt = f"{m['spearman_rho']:.3f}" if m["spearman_rho"] == m["spearman_rho"] else "undefined"
        sev_rows.append({"experiment": "E1 UPDRS-III in PD", "model": name, "n": m["n"],
                         "MAE": f"{m['mae']:.2f} ({ci['mae_ci95'][0]:.2f}-{ci['mae_ci95'][1]:.2f})",
                         "Spearman": rho_txt})
        print(sev_rows[-1])
    pd.DataFrame(sev_rows).to_csv(out / "tables" / "e1_updrs3_severity_in_pd.csv", index=False)

    (out / "results" / "clinical_baseline_results.json").write_text(
        json.dumps(results, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print("done")


if __name__ == "__main__":
    main()
