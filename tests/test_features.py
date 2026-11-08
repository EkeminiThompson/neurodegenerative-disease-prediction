import numpy as np

from ndpred.features import eeg


def _sine(f, sfreq=250.0, secs=4.0, n_win=3, n_ch=2):
    t = np.arange(int(sfreq * secs)) / sfreq
    x = np.sin(2 * np.pi * f * t)
    return np.tile(x, (n_win, n_ch, 1))


def test_alpha_dominates_for_10hz_sine():
    wf = eeg.window_features(_sine(10.0), 250.0)
    assert (wf["rel_alpha"] > 0.9).all()
    assert np.allclose(wf["paf"], 10.0, atol=0.6)


def test_relative_powers_sum_to_about_one():
    rng = np.random.default_rng(0)
    x = rng.standard_normal((2, 3, 1000))
    wf = eeg.window_features(x, 250.0)
    total = sum(wf[f"rel_{b}"] for b in eeg.BANDS)
    assert np.all(total <= 1.0 + 1e-9) and np.all(total > 0.9)


def test_spectral_entropy_orders_noise_above_tone():
    rng = np.random.default_rng(1)
    noise = eeg.window_features(rng.standard_normal((1, 1, 1000)), 250.0)["spec_entropy"]
    tone = eeg.window_features(_sine(10.0, n_win=1, n_ch=1), 250.0)["spec_entropy"]
    assert noise.mean() > tone.mean()


def test_participant_features_one_row_and_regions():
    x = _sine(10.0, n_win=5, n_ch=3)
    feats = eeg.participant_features(x, 250.0, ["Fz", "Cz", "Oz"], eeg.REGIONS_1020)
    assert "global_rel_alpha" in feats and "reg_occipital_rel_alpha" in feats
    assert "ch_CZ_rel_alpha" in feats
    assert all(np.isscalar(v) for v in feats.values())
