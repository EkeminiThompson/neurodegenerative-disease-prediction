import numpy as np

from ndpred.evaluation import metrics as M


def test_perfect_classifier():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    m = M.binary_metrics(y, p)
    assert m["roc_auc"] == 1.0 and m["sensitivity"] == 1.0 and m["specificity"] == 1.0


def test_ece_zero_when_perfectly_calibrated_bins():
    y = np.array([0] * 8 + [1] * 2)
    p = np.full(10, 0.2)
    assert abs(M.expected_calibration_error(y, p)) < 1e-9


def test_cluster_bootstrap_resamples_participants_and_brackets_estimate():
    rng = np.random.default_rng(0)
    groups = np.repeat(np.arange(40), 2)
    y = np.repeat(rng.integers(0, 2, 40), 2)
    p = np.clip(y * 0.4 + rng.random(80) * 0.6, 0, 1)
    lo, hi, n = M.cluster_bootstrap_ci(y, p, groups, "roc_auc", n_boot=300, seed=1)
    est = M.binary_metrics(y, p)["roc_auc"]
    assert lo <= est <= hi and n > 250


def test_ordinal_metrics_perfect_agreement():
    y = np.array([1, 2, 3, 2, 1, 3])
    m = M.ordinal_metrics(y, y)
    assert m["mae"] == 0 and m["quadratic_weighted_kappa"] == 1.0
