import numpy as np
import pandas as pd

from ndpred.data import bids
from ndpred.fusion.late import fuse_probabilities


def test_missing_modality_is_not_imputed():
    eeg = np.array([0.9, np.nan, 0.2])
    clin = np.array([0.7, 0.4, np.nan])
    fused = fuse_probabilities({"eeg": eeg, "clinical": clin})
    assert np.allclose(fused, [0.8, 0.4, 0.2])
    none = fuse_probabilities({"a": np.array([np.nan]), "b": np.array([np.nan])})
    assert np.isnan(none).all()


def test_ds007526_loader_maps_documented_columns(tmp_path):
    pd.DataFrame({
        "participant_id": ["sub-001", "sub-002"], "subject_id": ["HC1", "PD1"],
        "group": ["HC", "PD"], "updrs_part_iii": ["0", "20"], "updrs_total": ["1", "30"],
        "moca": ["30", "n/a"], "age": [60, 70], "sex": ["F", "M"],
        "disease_duration": ["n/a", "24"], "ledd": ["n/a", "300"],
        "pigd_score": ["n/a", "0.1"], "td_score": ["n/a", "0.2"], "ctt": ["n/a", "50"],
    }).to_csv(tmp_path / "participants.tsv", sep="\t", index=False)
    df = bids.load_ds007526(tmp_path)
    assert df["label"].tolist() == [0, 1]
    assert np.isnan(df.loc[1, "moca"]) and df.loc[1, "sex"] == 1


def test_ds002778_group_from_id_prefix(tmp_path):
    pd.DataFrame({
        "participant_id": ["sub-hc1", "sub-pd3"], "age": [54, 52], "gender": ["f", "f"],
        "hand": ["r", "r"], "MMSE": [30, 29], "NAART": [48, 44],
        "disease_duration": ["n/a", "9"], "rl_deficits": ["n/a", "R"], "notes": ["n/a", "n/a"],
    }).to_csv(tmp_path / "participants.tsv", sep="\t", index=False)
    df = bids.load_ds002778(tmp_path)
    assert df["group"].tolist() == ["HC", "PD"] and df["label"].tolist() == [0, 1]
