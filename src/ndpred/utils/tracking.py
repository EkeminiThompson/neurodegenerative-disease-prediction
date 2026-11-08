"""Lightweight, dependency-free experiment tracking (JSONL + config hash).

Each run appends one JSON line with the config, its hash, library versions, seed and
metrics. This is deliberately MLflow-free so any result in reports/ can be traced to
an exact configuration without a tracking server; swap in MLflow if you prefer.
"""

from __future__ import annotations

import hashlib
import json
import platform
import random
import time
from pathlib import Path

import numpy as np


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=_json_default).encode()
                          ).hexdigest()[:12]


def log_run(path: str | Path, name: str, config: dict, metrics: dict) -> dict:
    import pandas
    import sklearn

    rec = {
        "name": name, "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": config, "config_hash": config_hash(config), "metrics": metrics,
        "env": {"python": platform.python_version(), "numpy": np.__version__,
                "pandas": pandas.__version__, "sklearn": sklearn.__version__},
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(json.dumps(rec, default=_json_default) + "\n")
    return rec
