"""EEG loading and preprocessing with MNE-Python.

One fixed, documented pipeline is applied identically to every cohort so that
preprocessing differences cannot masquerade as cohort effects:

1. read raw file (.set EEGLAB or .bdf BioSemi)
2. keep EEG channels only; upper-case channel names
3. band-pass 1-45 Hz (FIR, zero-phase), notch at the recorded mains frequency
4. resample to 250 Hz
5. common-average reference
6. fixed-length, non-overlapping 4 s windows; windows exceeding a peak-to-peak
   amplitude threshold are dropped (rejection counts are logged, never imputed)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class EEGConfig:
    l_freq: float = 1.0
    h_freq: float = 45.0
    sfreq: float = 250.0
    window_s: float = 4.0
    reject_ptp_uv: float = 200.0
    min_windows: int = 10


def read_raw(path: str | Path):
    import mne

    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".set":
        return mne.io.read_raw_eeglab(path, preload=True, verbose="ERROR")
    if suffix == ".bdf":
        return mne.io.read_raw_bdf(path, preload=True, verbose="ERROR")
    raise ValueError(f"Unsupported EEG format: {suffix}")


def preprocess(raw, cfg: EEGConfig | None = None, mains_hz: float | None = None):
    """Return (windows[n_win, n_ch, n_samp] in uV, ch_names, qc dict)."""
    import mne

    cfg = cfg or EEGConfig()
    raw = raw.copy().pick(picks="eeg")
    raw.rename_channels({c: c.upper() for c in raw.ch_names})
    raw.filter(cfg.l_freq, cfg.h_freq, fir_design="firwin", phase="zero", verbose="ERROR")
    if mains_hz and mains_hz < cfg.h_freq + 20:
        raw.notch_filter([mains_hz], verbose="ERROR")
    raw.resample(cfg.sfreq, verbose="ERROR")
    raw.set_eeg_reference("average", projection=False, verbose="ERROR")
    events = mne.make_fixed_length_events(raw, duration=cfg.window_s)
    ep = mne.Epochs(raw, events, tmin=0.0, tmax=cfg.window_s - 1 / cfg.sfreq,
                    baseline=None, preload=True, verbose="ERROR")
    data = ep.get_data() * 1e6  # volts -> microvolts
    ptp = np.ptp(data, axis=-1).max(axis=-1)
    keep = ptp < cfg.reject_ptp_uv
    qc = {"n_windows_total": int(len(keep)), "n_windows_kept": int(keep.sum()),
          "fraction_rejected": float(1 - keep.mean()) if len(keep) else 1.0}
    return data[keep], list(ep.ch_names), qc


def usable(qc: dict, cfg: EEGConfig | None = None) -> bool:
    cfg = cfg or EEGConfig()
    return qc["n_windows_kept"] >= cfg.min_windows
