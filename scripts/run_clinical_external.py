#!/usr/bin/env python
"""Independent-cohort test of the age-confounding finding (metadata only, real data).

Models using age (+ sex) are fitted on ALL of ds007526 (HC younger than PD) and applied
unchanged to ds002778, where PD and HC are age-matched. If the full-cohort AUC of ~0.7 in
ds007526 reflected disease information, it should transfer; if it reflects the age
imbalance, it should fall to chance in an age-balanced independent cohort.
MoCA (ds007526) and MMSE (ds002778) are different instruments and are not used.
Development cohort and test cohort share no participants. Test-set n is small (31):
intervals are wide and are reported.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ndpred import SEED
from ndpred.data import bids
from ndpred.evaluation.metrics import cluster_bootstrap_ci
from ndpred.utils.tracking import log_run, set_seed


def main() -> None:
    set_seed(SEED)
    dev = bids.load_ds007526("data/raw/ds007526").dropna(subset=["age", "sex"])
    ext = bids.load_ds002778("data/raw/ds002778").dropna(subset=["age", "sex"])
    y_d, y_e = dev["label"].to_numpy(int), ext["label"].to_numpy(int)
    rows = []
    rng = np.random.default_rng(SEED)
    for name, cols in {"age": ["age"], "age+sex": ["age", "sex"], "sex": ["sex"]}.items():
        m = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=1000))
        m.fit(dev[cols], y_d)
        p = m.predict_proba(ext[cols])[:, 1]
        auc = roc_auc_score(y_e, p)
        lo, hi, _ = cluster_bootstrap_ci(y_e, p, ext["participant_id"].to_numpy(), n_boot=5000, seed=SEED)
        perm = [roc_auc_score(rng.permutation(y_e), p) for _ in range(5000)]
        pval = float((np.sum(np.abs(np.array(perm) - 0.5) >= abs(auc - 0.5)) + 1) / 5001)
        rows.append({"train": "ds007526 (n=%d)" % len(dev), "test": "ds002778 (n=%d)" % len(ext),
                     "features": name, "auc": auc, "ci_lo": lo, "ci_hi": hi, "perm_p": pval,
                     "dev_auc_apparent": roc_auc_score(y_d, m.predict_proba(dev[cols])[:, 1])})
    out = pd.DataFrame(rows)
    # descriptive balance in both cohorts
    bal = []
    for nm, d in (("ds007526", dev), ("ds002778", ext)):
        a1, a0 = d.loc[d.label == 1, "age"], d.loc[d.label == 0, "age"]
        t = stats.ttest_ind(a1, a0, equal_var=False)
        bal.append({"cohort": nm, "n_PD": len(a1), "n_HC": len(a0), "age_PD": a1.mean(), "age_HC": a0.mean(),
                    "welch_p": t.pvalue, "age_only_auc_in_cohort": roc_auc_score(d.label, d.age)})
    bal = pd.DataFrame(bal)
    Path("reports/tables").mkdir(parents=True, exist_ok=True)
    out.to_csv("reports/tables/x1_clinical_external_ds002778.csv", index=False)
    bal.to_csv("reports/tables/x1_age_balance_by_cohort.csv", index=False)
    print(out.round(3).to_string(index=False))
    print(bal.round(3).to_string(index=False))
    log_run("reports/results/runs.jsonl", "X1_clinical_external", {"train": "ds007526", "test": "ds002778", "seed": SEED},
            {"external": out.to_dict("records"), "balance": bal.to_dict("records")})


if __name__ == "__main__":
    main()
