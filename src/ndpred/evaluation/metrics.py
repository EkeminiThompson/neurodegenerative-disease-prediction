"""Metrics with participant-level (cluster) bootstrap confidence intervals."""

from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    cohen_kappa_score,
    confusion_matrix,
    mean_absolute_error,
    roc_auc_score,
)


def expected_calibration_error(y, p, n_bins: int = 10) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    edges = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            ece += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(ece)


def reliability_table(y, p, n_bins: int = 10):
    y, p = np.asarray(y, float), np.asarray(p, float)
    edges = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
    rows = []
    for b in range(n_bins):
        m = idx == b
        if m.any():
            rows.append({"bin": b, "n": int(m.sum()),
                         "mean_predicted": float(p[m].mean()),
                         "observed_rate": float(y[m].mean())})
    return rows


def binary_metrics(y, p, threshold: float = 0.5) -> dict:
    y, p = np.asarray(y).astype(int), np.asarray(p, float)
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    sens = tp / (tp + fn) if tp + fn else np.nan
    spec = tn / (tn + fp) if tn + fp else np.nan
    prec = tp / (tp + fp) if tp + fp else np.nan
    f1 = 2 * prec * sens / (prec + sens) if prec == prec and sens == sens and prec + sens else np.nan
    two_class = len(np.unique(y)) == 2
    return {
        "n": int(len(y)), "n_pos": int(y.sum()),
        "accuracy": (tp + tn) / len(y),
        "balanced_accuracy": np.nanmean([sens, spec]),
        "precision": prec, "recall": sens, "sensitivity": sens, "specificity": spec, "f1": f1,
        "roc_auc": roc_auc_score(y, p) if two_class else np.nan,
        "pr_auc": average_precision_score(y, p) if two_class else np.nan,
        "brier": brier_score_loss(y, p), "ece": expected_calibration_error(y, p),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def ordinal_metrics(y_true, y_pred) -> dict:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    out = {"n": int(len(y_true)), "mae": float(mean_absolute_error(y_true, y_pred))}
    rho = spearmanr(y_true, y_pred)
    out["spearman_rho"] = float(rho.statistic)
    if np.allclose(y_true, np.round(y_true)) and np.allclose(y_pred, np.round(y_pred)):
        out["weighted_kappa_linear"] = float(cohen_kappa_score(y_true, y_pred, weights="linear"))
        out["quadratic_weighted_kappa"] = float(
            cohen_kappa_score(y_true, y_pred, weights="quadratic"))
    return out


def cluster_bootstrap_ci(y, p, groups, metric: str = "roc_auc", n_boot: int = 2000,
                         seed: int = 0, alpha: float = 0.05):
    """95% CI by resampling whole participants (groups), never single rows."""
    y, p, groups = np.asarray(y), np.asarray(p, float), np.asarray(groups)
    ug = np.unique(groups)
    members = {g: np.where(groups == g)[0] for g in ug}
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(n_boot):
        pick = rng.choice(ug, size=len(ug), replace=True)
        idx = np.concatenate([members[g] for g in pick])
        if len(np.unique(y[idx])) < 2:
            continue
        stats.append(binary_metrics(y[idx], p[idx])[metric])
    stats = np.asarray(stats, float)
    lo, hi = np.nanpercentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi), int(len(stats))


def summarise_with_ci(y, p, groups, metrics=("roc_auc", "pr_auc", "balanced_accuracy",
                                              "sensitivity", "specificity", "brier"),
                      n_boot: int = 2000, seed: int = 0) -> dict:
    base = binary_metrics(y, p)
    out = dict(base)
    for m in metrics:
        lo, hi, nb = cluster_bootstrap_ci(y, p, groups, m, n_boot, seed)
        out[f"{m}_ci95"] = (lo, hi)
        out["n_boot_valid"] = nb
    return out
