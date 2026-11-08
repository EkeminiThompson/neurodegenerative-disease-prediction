"""Baseline classifiers/regressors wrapped in leakage-safe pipelines.

Every pipeline = median imputation (+ missing-indicator off by default, so no value is
invented beyond the median of the TRAINING fold) -> standardisation -> optional
univariate feature selection -> estimator. All steps are fitted on training folds only.
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

CLASSIFIERS = ("logreg", "rf", "svm", "xgboost", "lightgbm")


class BalancedXGB(BaseEstimator, ClassifierMixin):
    """XGBoost with scale_pos_weight set from the training labels at fit time."""

    def __init__(self, n_estimators=300, max_depth=3, learning_rate=0.05,
                 subsample=0.8, colsample_bytree=0.8, random_state=0):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state

    def fit(self, X, y):
        from xgboost import XGBClassifier

        y = np.asarray(y)
        pos = max(int(y.sum()), 1)
        self.classes_ = np.unique(y)
        self.model_ = XGBClassifier(
            n_estimators=self.n_estimators, max_depth=self.max_depth,
            learning_rate=self.learning_rate, subsample=self.subsample,
            colsample_bytree=self.colsample_bytree, random_state=self.random_state,
            scale_pos_weight=(len(y) - pos) / pos, eval_metric="logloss", n_jobs=1,
            verbosity=0)
        self.model_.fit(X, y)
        return self

    def predict_proba(self, X):
        return self.model_.predict_proba(X)

    def predict(self, X):
        return self.model_.predict(X)


def _classifier(name: str, seed: int):
    if name == "logreg":
        return LogisticRegression(C=0.5, class_weight="balanced", max_iter=5000,
                                  random_state=seed)
    if name == "rf":
        return RandomForestClassifier(n_estimators=500, min_samples_leaf=2,
                                      class_weight="balanced_subsample", random_state=seed,
                                      n_jobs=1)
    if name == "svm":
        return SVC(kernel="rbf", C=1.0, class_weight="balanced", probability=True,
                   random_state=seed)
    if name == "xgboost":
        return BalancedXGB(random_state=seed)
    if name == "lightgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=8,
                              min_child_samples=5, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, class_weight="balanced",
                              random_state=seed, n_jobs=1, verbose=-1)
    raise ValueError(f"Unknown classifier {name!r}; choose from {CLASSIFIERS}")


def make_classifier(name: str, seed: int = 0, k_features: int | None = None) -> Pipeline:
    steps = [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    if k_features:
        steps.append(("select", SelectKBest(f_classif, k=k_features)))
    steps.append(("clf", _classifier(name, seed)))
    return Pipeline(steps)


def make_regressor(name: str = "ridge", seed: int = 0, k_features: int | None = None) -> Pipeline:
    steps = [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    if k_features:
        steps.append(("select", SelectKBest(f_regression, k=k_features)))
    est = Ridge(alpha=10.0) if name == "ridge" else RandomForestRegressor(
        n_estimators=500, min_samples_leaf=2, random_state=seed, n_jobs=1)
    steps.append(("reg", est))
    return Pipeline(steps)
