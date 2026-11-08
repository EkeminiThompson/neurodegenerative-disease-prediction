"""Independent external validation and domain-shift diagnostics.

The model is fitted on the development cohort ONLY. The external cohort is touched
exactly once, for prediction. Optional per-cohort standardisation uses feature values
only (never labels) and is reported as a separate, clearly labelled condition because it
is transductive with respect to the external cohort's feature distribution.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .metrics import summarise_with_ci


def zscore_within_cohort(X: pd.DataFrame) -> pd.DataFrame:
    sd = X.std(ddof=0).replace(0, np.nan)
    return (X - X.mean()) / sd


def external_validate(estimator, X_dev, y_dev, X_ext, y_ext, ext_groups,
                      n_boot: int = 2000, seed: int = 0) -> dict:
    cols = [c for c in X_dev.columns if c in X_ext.columns]
    if not cols:
        raise ValueError("No shared features between development and external cohorts")
    est = clone(estimator).fit(X_dev[cols], np.asarray(y_dev))
    p = est.predict_proba(X_ext[cols])[:, 1]
    res = summarise_with_ci(np.asarray(y_ext), p, np.asarray(ext_groups), n_boot=n_boot,
                            seed=seed)
    res["n_shared_features"] = len(cols)
    res["predictions"] = p
    return res


def standardized_mean_differences(Xa: pd.DataFrame, Xb: pd.DataFrame) -> pd.Series:
    cols = [c for c in Xa.columns if c in Xb.columns]
    pooled = np.sqrt((Xa[cols].var(ddof=1) + Xb[cols].var(ddof=1)) / 2).replace(0, np.nan)
    return ((Xa[cols].mean() - Xb[cols].mean()) / pooled).sort_values(key=np.abs, ascending=False)


def domain_classifier_auc(Xa: pd.DataFrame, Xb: pd.DataFrame, seed: int = 0) -> float:
    """Cross-validated AUC of a classifier separating cohort A from B.

    ~0.5: cohorts are feature-indistinguishable; ->1.0: severe domain shift.
    """
    cols = [c for c in Xa.columns if c in Xb.columns]
    X = pd.concat([Xa[cols], Xb[cols]], ignore_index=True)
    X = X.fillna(X.median())
    d = np.r_[np.zeros(len(Xa)), np.ones(len(Xb))]
    n_splits = int(min(5, np.bincount(d.astype(int)).min()))
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000, C=0.1))
    pred = cross_val_predict(clf, X, d, cv=StratifiedKFold(n_splits, shuffle=True,
                                                           random_state=seed),
                             method="predict_proba")[:, 1]
    return float(roc_auc_score(d, pred))
