"""SHAP explanations for fitted sklearn Pipelines (tree, linear, or kernel fallback)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _transform_until_last(pipe, X: pd.DataFrame):
    Z, names = X, list(X.columns)
    for name, step in pipe.steps[:-1]:
        Z = step.transform(Z)
        if name == "select":
            names = [n for n, keep in zip(names, step.get_support()) if keep]
    return np.asarray(Z), names


def mean_abs_shap(pipe, X_background: pd.DataFrame, X_explain: pd.DataFrame,
                  max_background: int = 50) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """Return (global importance table, per-sample SHAP matrix, feature names).

    ``pipe`` must already be fitted. Background data should come from the training set.
    """
    import shap

    Zb, names = _transform_until_last(pipe, X_background)
    Ze, _ = _transform_until_last(pipe, X_explain)
    est = pipe.steps[-1][1]
    model = getattr(est, "model_", est)
    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(Ze)
    except Exception:
        try:
            explainer = shap.LinearExplainer(model, Zb)
            sv = explainer.shap_values(Ze)
        except Exception:
            bg = shap.sample(Zb, min(max_background, len(Zb)), random_state=0)
            explainer = shap.KernelExplainer(lambda z: est.predict_proba(z)[:, 1], bg)
            sv = explainer.shap_values(Ze, nsamples=200)
    if isinstance(sv, list):
        sv = sv[-1]
    sv = np.asarray(sv)
    if sv.ndim == 3:
        sv = sv[..., -1]
    table = (pd.DataFrame({"feature": names, "mean_abs_shap": np.abs(sv).mean(0)})
             .sort_values("mean_abs_shap", ascending=False).reset_index(drop=True))
    return table, sv, names
