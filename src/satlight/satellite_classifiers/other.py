"""Classifier: catch-all fallback for everything else."""

from __future__ import annotations

CLASSIFICATION = "OTHER"
PRIORITY = 1000


def matches(name: str, norad_id: int) -> bool:
    return True
