"""EEG feature extraction (pure NumPy/SciPy; operates on windowed arrays).

Input arrays have shape (n_windows, n_channels, n_samples) in microvolts.
Windows are always aggregated to ONE row per participant (median across windows)
before any model sees them, so windows from one participant can never straddle a
train/test boundary.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import welch

BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}
TOTAL_RANGE = (1.0, 45.0)


def psd(x: np.ndarray, sfreq: float, nperseg: int | None = None):
    """Welch PSD along the last axis. Returns (freqs, psd[..., n_freqs])."""
    nperseg = nperseg or int(min(x.shape[-1], 2 * sfreq))
    return welch(x, fs=sfreq, nperseg=nperseg, noverlap=nperseg // 2, axis=-1)


def _band_mask(freqs, lo, hi):
    return (freqs >= lo) & (freqs < hi)


def band_powers(freqs: np.ndarray, p: np.ndarray) -> dict[str, np.ndarray]:
    """Absolute and relative band power; arrays shaped like p[..., 0]."""
    df = freqs[1] - freqs[0]
    total = p[..., _band_mask(freqs, *TOTAL_RANGE)].sum(-1) * df
    out = {}
    for name, (lo, hi) in BANDS.items():
        a = p[..., _band_mask(freqs, lo, hi)].sum(-1) * df
        out[f"abs_{name}"] = a
        out[f"rel_{name}"] = a / np.maximum(total, 1e-12)
    return out


def spectral_entropy(freqs: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Normalised Shannon entropy of the 1-45 Hz PSD (0..1)."""
    q = p[..., _band_mask(freqs, *TOTAL_RANGE)]
    q = q / np.maximum(q.sum(-1, keepdims=True), 1e-12)
    h = -(q * np.log(np.maximum(q, 1e-12))).sum(-1)
    return h / np.log(q.shape[-1])


def hjorth(x: np.ndarray):
    """Hjorth activity, mobility, complexity along the last axis."""
    dx = np.diff(x, axis=-1)
    ddx = np.diff(dx, axis=-1)
    v0, v1, v2 = x.var(-1), dx.var(-1), ddx.var(-1)
    mobility = np.sqrt(v1 / np.maximum(v0, 1e-12))
    complexity = np.sqrt(v2 / np.maximum(v1, 1e-12)) / np.maximum(mobility, 1e-12)
    return v0, mobility, complexity


def peak_alpha_frequency(freqs: np.ndarray, p: np.ndarray) -> np.ndarray:
    m = _band_mask(freqs, 6.0, 13.0)
    return freqs[m][np.argmax(p[..., m], axis=-1)]


def window_features(x: np.ndarray, sfreq: float) -> dict[str, np.ndarray]:
    """Per-window, per-channel features; each value has shape (n_windows, n_channels)."""
    freqs, p = psd(x, sfreq)
    f = band_powers(freqs, p)
    f["spec_entropy"] = spectral_entropy(freqs, p)
    f["paf"] = peak_alpha_frequency(freqs, p)
    act, mob, comp = hjorth(x)
    f["hjorth_activity"], f["hjorth_mobility"], f["hjorth_complexity"] = act, mob, comp
    f["theta_beta_ratio"] = f["abs_theta"] / np.maximum(f["abs_beta"], 1e-12)
    f["alpha_theta_ratio"] = f["abs_alpha"] / np.maximum(f["abs_theta"], 1e-12)
    return f


def participant_features(
    x: np.ndarray,
    sfreq: float,
    ch_names: list[str],
    regions: dict[str, list[str]] | None = None,
    core_channels: list[str] | None = None,
) -> dict[str, float]:
    """One feature vector per recording: median over windows, then channel / region level.

    ``regions`` maps region name -> channel names (case-insensitive). Region
    features average channel medians and are the recommended cross-cohort
    representation because montages differ between cohorts.
    """
    wf = window_features(x, sfreq)
    names = [c.upper() for c in ch_names]
    out: dict[str, float] = {}
    for key, arr in wf.items():
        med = np.median(arr, axis=0)  # (n_channels,)
        out[f"global_{key}"] = float(np.mean(med))
        if core_channels:
            ci_core = [names.index(c.upper()) for c in core_channels if c.upper() in names]
            if ci_core:
                out[f"core_{key}"] = float(np.mean(med[ci_core]))
        for ci, ch in enumerate(names):
            out[f"ch_{ch}_{key}"] = float(med[ci])
        for rname, chans in (regions or {}).items():
            idx = [names.index(c.upper()) for c in chans if c.upper() in names]
            if idx:
                out[f"reg_{rname}_{key}"] = float(np.mean(med[idx]))
    return out


# Coarse regions defined on the standard 10-20 / 10-10 labels common to both cohorts.
REGIONS_1020 = {
    "frontal": ["Fp1", "Fp2", "F3", "F4", "F7", "F8", "Fz"],
    "central": ["C3", "C4"],  # Cz omitted: it is the recording reference (VREF) in ds007526
    "temporal": ["T7", "T8", "T3", "T4"],
    "parietal": ["P3", "P4", "Pz", "P7", "P8"],
    "occipital": ["O1", "O2", "Oz"],
}


# Scalp channels present in BOTH ds007526 (65-ch EGI) and ds002778 (40-ch BioSemi), verified from
# the two cohorts' channels.tsv files. Cross-cohort features are averaged over exactly this set so
# that montage differences cannot create a cohort effect. (ds002778's extra Cz is excluded.)
CORE_CHANNELS = [
    "Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3", "CP1", "CP5", "P7", "P3", "Pz", "PO3",
    "O1", "Oz", "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8", "FC6", "FC2", "F4", "F8",
    "AF4", "Fp2", "Fz",
]
