"""Projection mode: full sky (whole celestial sphere, visible and hidden)."""

from __future__ import annotations

MODE = {
    "id": "full_sky",
    "label": "FULL SKY",
    "description": "Full sphere projection showing visible and below-horizon "
    "satellites together.",
    "order": 20,
    "default": False,
    "horizon_ring": False,
}
