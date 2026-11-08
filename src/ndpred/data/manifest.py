"""Dataset provenance: checksums and manifests (no raw data is ever copied)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def write_manifest(path: str | Path, manifest: dict) -> None:
    Path(path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def verify_files(root: str | Path, expected: dict[str, str]) -> dict[str, bool]:
    """Compare sha256 of files under ``root`` with a {relative_path: sha256} map."""
    root = Path(root)
    return {rel: (root / rel).exists() and sha256(root / rel) == digest
            for rel, digest in expected.items()}
