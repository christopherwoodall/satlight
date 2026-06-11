"""Classifier: International Space Station."""

from __future__ import annotations

CLASSIFICATION = "ISS"
PRIORITY = 5

_ISS_NORAD_ID = 25544


def matches(name: str, norad_id: int) -> bool:
    return norad_id == _ISS_NORAD_ID or "ISS (ZARYA)" in name.upper()
