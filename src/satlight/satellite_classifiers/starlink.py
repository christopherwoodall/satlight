"""Classifier: SpaceX Starlink constellation."""

from __future__ import annotations

CLASSIFICATION = "STARLINK"
PRIORITY = 10


def matches(name: str, norad_id: int) -> bool:
    return name.upper().startswith("STARLINK")
