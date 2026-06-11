"""Offline nearest-city lookup for the satellite ground point.

Loads a compact list of major world cities (bundled asset) and answers
"which city is this sub-satellite point over?" with a simple great-circle search.
Used only on demand when a client hovers a satellite, so the per-frame stream
stays untouched.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

_DEG = math.pi / 180.0


@dataclass(frozen=True, slots=True)
class City:
    name: str
    country: str
    cc: str
    lat: float
    lon: float


class CityIndex:
    def __init__(self, cities: list[City]) -> None:
        self._cities = cities

    @classmethod
    def load(cls, path: Path) -> CityIndex:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls([])
        cities = [
            City(c["name"], c.get("country", ""), c.get("cc", ""), c["lat"], c["lon"])
            for c in raw
        ]
        return cls(cities)

    def nearest(self, lat: float, lon: float) -> City | None:
        if not self._cities:
            return None

        cos_lat = math.cos(lat * _DEG)

        best: City | None = None
        best_d = float("inf")
        for city in self._cities:
            dlat = (city.lat - lat) * _DEG
            dlon = (city.lon - lon) * _DEG
            # Cheap equirectangular approximation (good enough for nearest-of-N).
            x = dlon * cos_lat
            d = x * x + dlat * dlat
            if d < best_d:
                best_d = d
                best = city
        return best
