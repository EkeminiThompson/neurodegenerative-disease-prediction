import numpy as np
import pytest

mne = pytest.importorskip("mne")

from ndpred.features.eeg import participant_features  # noqa: E402
from ndpred.preprocessing.eeg import EEGConfig, preprocess, usable  # noqa: E402


def _toy_raw(sfreq=512.0, secs=120.0):
    rng = np.random.default_rng(0)
    t = np.arange(int(sfreq * secs)) / sfreq
    chs = ["Fz", "Cz", "Pz", "Oz"]
    amp = np.array([0.0, 0.0, 0.0, 20e-6])[:, None]  # alpha only at Oz (CAR-safe)
    data = amp * np.sin(2 * np.pi * 10 * t)[None] + 2e-6 * rng.standard_normal((4, t.size))
    info = mne.create_info(chs, sfreq, "eeg")
    return mne.io.RawArray(data, info, verbose="ERROR")


def test_preprocess_resamples_windows_and_reports_qc():
    win, names, qc = preprocess(_toy_raw(), EEGConfig(), mains_hz=None)
    assert win.shape[1:] == (4, 1000) and names == ["FZ", "CZ", "PZ", "OZ"]
    assert qc["n_windows_kept"] == win.shape[0] and usable(qc)
    feats = participant_features(win, 250.0, names)
    assert feats["ch_OZ_rel_alpha"] > 0.5
