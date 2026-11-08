"""Group-aware repeated cross-validation (participant-level, leakage-safe)."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedGroupKFold


def assert_no_group_overlap(train_groups, test_groups) -> None:
    overlap = set(train_groups) & set(test_groups)
    if overlap:
        raise AssertionError(f"Participant leakage: {sorted(overlap)[:5]} in both train and test")


def repeated_group_cv(
    estimator_factory: Callable[[], object],
    X: pd.DataFrame,
    y,
    groups,
    n_splits: int = 5,
    n_repeats: int = 10,
    seed: int = 0,
    regression: bool = False,
) -> pd.DataFrame:
    """Out-of-fold predictions for every repeat.

    Returns a long DataFrame [repeat, row, group, y, pred]. Imputation, scaling,
    feature selection and any hyper-parameter search live inside the estimator,
    so they are re-fit on each training fold only.
    """
    X = X.reset_index(drop=True)
    y, groups = np.asarray(y), np.asarray(groups)
    records = []
    for r in range(n_repeats):
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + r)
        strat = y if not regression else pd.qcut(y, q=min(4, len(np.unique(y))),
                                                 labels=False, duplicates="drop")
        for tr, te in splitter.split(X, strat, groups):
            assert_no_group_overlap(groups[tr], groups[te])
            est = clone(estimator_factory())
            if hasattr(est, "cv") and hasattr(est, "param_grid"):  # nested: inner search
                est.fit(X.iloc[tr], y[tr], groups=groups[tr])
            else:
                est.fit(X.iloc[tr], y[tr])
            pred = est.predict(X.iloc[te]) if regression else est.predict_proba(X.iloc[te])[:, 1]
            records.append(pd.DataFrame({"repeat": r, "row": te, "group": groups[te],
                                         "y": y[te], "pred": pred}))
    return pd.concat(records, ignore_index=True)


def average_over_repeats(oof: pd.DataFrame) -> pd.DataFrame:
    """One prediction per row: mean of that row's out-of-fold predictions."""
    return (oof.groupby("row").agg(group=("group", "first"), y=("y", "first"),
                                   pred=("pred", "mean")).reset_index())
