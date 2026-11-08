#!/usr/bin/env python
"""Figures from the saved real-data results (reports/results/clinical_baseline_results.json)."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

res = json.loads(Path("reports/results/clinical_baseline_results.json").read_text())
out = Path("reports/figures")
out.mkdir(parents=True, exist_ok=True)

rows = [(k, v) for k, v in res.items() if k.startswith("E0/")]
rows.sort(key=lambda kv: (kv[0].split("/")[1], kv[0].split("/")[2]))
labels = [f"{k.split('/')[1].replace('_', ' ')} | {k.split('/')[2]}" for k, _ in rows]
est = [v["roc_auc"] for _, v in rows]
lo = [v["roc_auc_ci95"][0] for _, v in rows]
hi = [v["roc_auc_ci95"][1] for _, v in rows]

fig, ax = plt.subplots(figsize=(7.5, 5))
ypos = range(len(rows))
colors = ["#4C72B0" if "age only" in lab else "#DD8452" for lab in labels]
ax.hlines(list(ypos), lo, hi, color=colors, lw=2)
ax.scatter(est, list(ypos), color=colors, zorder=3)
ax.axvline(0.5, color="grey", ls="--", lw=1)
ax.set_yticks(list(ypos))
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel("ROC-AUC (95% participant-level bootstrap CI)")
ax.set_title("E0: PD vs HC from clinical metadata only\nds007526, n=144 (116 PD / 28 HC), "
             "repeated grouped 5-fold CV", fontsize=10)
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(out / "e0_clinical_auc_forest.png", dpi=200)
print("wrote", out / "e0_clinical_auc_forest.png")


# ---- A3: age-matched sensitivity (reports/tables/a3_age_matched_sensitivity.csv) ----
import pandas as pd  # noqa: E402

a3 = pd.read_csv("reports/tables/a3_age_matched_sensitivity.csv")
a3["label"] = a3["features"].str.replace("_", " ") + " | " + a3["model"]
fig, ax = plt.subplots(figsize=(7, 3.6))
ypos = list(range(len(a3)))
ax.hlines(ypos, a3["ci_lo"], a3["ci_hi"], color="#DD8452", lw=2)
ax.scatter(a3["roc_auc"], ypos, color="#DD8452", zorder=3)
ax.axvline(0.5, color="grey", ls="--", lw=1)
ax.set_yticks(ypos)
ax.set_yticklabels(a3["label"], fontsize=8)
ax.set_xlim(0, 1)
ax.set_xlabel("ROC-AUC (95% participant-level bootstrap CI)")
ax.set_title("A3: age-matched subset of ds007526 (n=54; 27 PD / 27 HC; mean age 61.6 vs 61.3 y)",
             fontsize=9)
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(out / "a3_age_matched_forest.png", dpi=200)
print("wrote", out / "a3_age_matched_forest.png")
