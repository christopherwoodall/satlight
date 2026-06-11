"""Projection mode: ceiling (zenith at center, horizon at the screen edge)."""

from __future__ import annotations

MODE = {
    "id": "ceiling",
    "label": "CEILING",
    "description": "Zenith centered overhead; horizon at the edge. "
    "Below-horizon satellites clamp to a dim horizon ring.",
    "order": 10,
    "default": True,
    "horizon_ring": True,
}
