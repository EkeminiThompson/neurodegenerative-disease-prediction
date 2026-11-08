"""Late fusion with explicit missing-modality handling (no fabricated observations).

Each modality has its own model. For a participant, the fused probability is the
(optionally weighted) mean of the probabilities from the modalities that were actually
observed for that participant. A modality that is absent contributes nothing; it is
never imputed. Participants with no observed modality get NaN and are excluded from
metrics, and the count is reported.
"""

from __future__ import annotations

import numpy as np


def fuse_probabilities(prob_by_modality: dict[str, np.ndarray],
                       weights: dict[str, float] | None = None) -> np.ndarray:
    names = list(prob_by_modality)
    P = np.vstack([np.asarray(prob_by_modality[m], float) for m in names])  # (M, N)
    w = np.array([(weights or {}).get(m, 1.0) for m in names], float)[:, None]
    observed = ~np.isnan(P)
    num = np.where(observed, P * w, 0.0).sum(0)
    den = np.where(observed, w, 0.0).sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        fused = np.where(den > 0, num / den, np.nan)
    return fused
