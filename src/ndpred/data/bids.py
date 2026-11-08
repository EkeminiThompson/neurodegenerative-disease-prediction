"""Loaders for the public BIDS metadata of the Parkinson's EEG cohorts.

Only documented columns are read. No label is inferred: PD/HC comes from the
dataset's own ``group`` column (ds007526) or from the documented participant-ID
prefix ``sub-hc*`` / ``sub-pd*`` (ds002778, where the README names the groups).
Missing values stay missing (NaN).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

LABEL_MAP = {"HC": 0, "PD": 1}


def _read_participants(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / "participants.tsv", sep="\t", na_values=["n/a"])


def load_ds007526(root: str | Path) -> pd.DataFrame:
    """PD-EEG (Tel Aviv Sourasky), OpenNeuro ds007526 v1.0.2."""
    root = Path(root)
    p = _read_participants(root)
    out = pd.DataFrame(
        {
            "participant_id": p["participant_id"],
            "cohort": "ds007526",
            "group": p["group"].str.upper(),
            "age": p["age"],
            "sex": p["sex"].str.upper().map({"F": 0, "M": 1}),
            "moca": p["moca"],
            "updrs_iii": p["updrs_part_iii"],
            "updrs_total": p["updrs_total"],
            "disease_duration": p["disease_duration"],  # unit not documented upstream
            "ledd": p["ledd"],
        }
    )
    out["label"] = out["group"].map(LABEL_MAP)
    return out


def load_ds002778(root: str | Path) -> pd.DataFrame:
    """UC San Diego resting-state EEG, OpenNeuro ds002778 v1.0.5.

    Group is taken from the participant-ID prefix, which the dataset uses
    consistently (sub-hc*, sub-pd*). H&Y and UPDRS are read per session from the
    ``beh`` JSON sidecars (PD only; ON and OFF medication sessions).
    """
    root = Path(root)
    p = _read_participants(root)
    grp = p["participant_id"].str.extract(r"sub-(hc|pd)", expand=False).str.upper()
    out = pd.DataFrame(
        {
            "participant_id": p["participant_id"],
            "cohort": "ds002778",
            "group": grp,
            "age": p["age"],
            "sex": p["gender"].str.lower().map({"f": 0, "m": 1}),
            "mmse": p["MMSE"],
            "naart": p["NAART"],
            "disease_duration": p["disease_duration"],  # years for this cohort
        }
    )
    out["label"] = out["group"].map(LABEL_MAP)
    return out


def load_ds002778_sessions(root: str | Path) -> pd.DataFrame:
    """Per-session (ON/OFF) UPDRS and Hoehn & Yahr for ds002778 PD participants."""
    root = Path(root)
    rows = []
    for f in sorted(root.glob("sub-pd*/ses-*/beh/*_beh.json")):
        sub = f.parts[-4]
        ses = f.parts[-3].replace("ses-", "")
        q = json.loads(f.read_text()).get("questionairres", {})
        rows.append(
            {
                "participant_id": sub,
                "session": ses,
                "hoehn_yahr": _num(q.get("H&Y")),
                "updrs_total": _num(q.get("Total UPDRS")),
            }
        )
    return pd.DataFrame(rows)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan
