import numpy as np
import pandas as pd

from ndpred.evaluation.external import (
    domain_classifier_auc,
    external_validate,
    standardized_mean_differences,
    zscore_within_cohort,
)
from ndpred.models.baselines import make_classifier


def _toy(n, shift, seed):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, n)
    X = pd.DataFrame({"a": rng.standard_normal(n) + y + shift, "b": rng.standard_normal(n)})
    return X, y


def test_domain_classifier_detects_shift_and_not_identity():
    Xa, _ = _toy(80, 0.0, 0)
    Xb_shifted, _ = _toy(80, 4.0, 1)
    Xb_same, _ = _toy(80, 0.0, 2)
    assert domain_classifier_auc(Xa, Xb_shifted) > 0.9
    assert domain_classifier_auc(Xa, Xb_same) < 0.7


def test_external_validation_uses_only_shared_features_and_cohort_z_helps_shift():
    Xa, ya = _toy(120, 0.0, 3)
    Xb, yb = _toy(120, 3.0, 4)
    Xb["extra_only_in_b"] = 1.0
    est = make_classifier("logreg", 0)
    res = external_validate(est, Xa, ya, Xb, yb, np.arange(len(yb)), n_boot=200, seed=0)
    assert res["n_shared_features"] == 2
    z = external_validate(est, zscore_within_cohort(Xa), ya, zscore_within_cohort(Xb[["a", "b"]]),
                          yb, np.arange(len(yb)), n_boot=200, seed=0)
    assert z["roc_auc"] > 0.7


def test_smd_ranks_shifted_feature_first():
    Xa, _ = _toy(100, 0.0, 5)
    Xb, _ = _toy(100, 3.0, 6)
    assert standardized_mean_differences(Xa, Xb).index[0] == "a"
