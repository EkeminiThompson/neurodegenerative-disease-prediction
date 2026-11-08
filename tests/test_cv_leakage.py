import numpy as np
import pandas as pd
import pytest

from ndpred.evaluation.cv import assert_no_group_overlap, repeated_group_cv
from ndpred.models.baselines import make_classifier


def test_overlap_detector_raises():
    with pytest.raises(AssertionError):
        assert_no_group_overlap(["a", "b"], ["b", "c"])


def test_repeated_cv_never_splits_a_participant_with_multiple_recordings():
    rng = np.random.default_rng(0)
    n_sub, rec = 30, 3  # three recordings per participant
    groups = np.repeat([f"s{i}" for i in range(n_sub)], rec)
    y = np.repeat(rng.integers(0, 2, n_sub), rec)
    X = pd.DataFrame(rng.standard_normal((n_sub * rec, 2)), columns=["f1", "f2"])
    oof = repeated_group_cv(lambda: make_classifier("logreg", 0), X, y, groups, 5, 2, 0)
    # every row predicted exactly once per repeat
    assert oof.groupby("repeat")["row"].apply(lambda r: r.is_unique).all()
    assert len(oof) == 2 * len(X)


def test_selection_is_inside_pipeline():
    pipe = make_classifier("logreg", 0, k_features=2)
    assert [n for n, _ in pipe.steps] == ["impute", "scale", "select", "clf"]
