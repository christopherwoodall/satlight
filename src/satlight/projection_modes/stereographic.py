"""Projection mode: stereographic (azimuthal, low distortion near the horizon)."""

from __future__ import annotations

MODE = {
    "id": "stereographic",
    "label": "STEREO",
    "description": "Azimuthal stereographic dome. Zenith centered; less "
    "compression near the horizon than the ceiling mode.",
    "order": 30,
    "default": False,
    "horizon_ring": True,
}
