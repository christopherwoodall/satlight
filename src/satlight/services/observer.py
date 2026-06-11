"""Observer location store.

``settings.json`` is the single mutable runtime value in SatLight. It is seeded
from the hardcoded defaults in :mod:`satlight.config` on first run and is the
source of truth afterwards. Updates are written atomically and applied in-memory
immediately, so changes take effect with no restart.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from ..config import (
    DEFAULT_OBSERVER_ELEVATION_M,
    DEFAULT_OBSERVER_LATITUDE,
    DEFAULT_OBSERVER_LONGITUDE,
    Config,
)


@dataclass(frozen=True, slots=True)
class Observer:
    latitude: float
    longitude: float
    elevation_m: float


class ObserverStore:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._observer = self._load()

    def _load(self) -> Observer:
        path = self._cfg.settings_path
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return Observer(
                    latitude=float(data["latitude"]),
                    longitude=float(data["longitude"]),
                    elevation_m=float(data["elevation_m"]),
                )
            except (OSError, ValueError, KeyError):
                pass

        observer = Observer(
            latitude=DEFAULT_OBSERVER_LATITUDE,
            longitude=DEFAULT_OBSERVER_LONGITUDE,
            elevation_m=DEFAULT_OBSERVER_ELEVATION_M,
        )
        self._save(observer)
        return observer

    def _save(self, observer: Observer) -> None:
        path = self._cfg.settings_path
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(observer), indent=2))
        tmp.replace(path)

    @property
    def current(self) -> Observer:
        return self._observer

    def update(self, latitude: float, longitude: float, elevation_m: float) -> Observer:
        latitude = max(-90.0, min(90.0, float(latitude)))
        longitude = ((float(longitude) + 180.0) % 360.0) - 180.0
        observer = Observer(latitude, longitude, float(elevation_m))
        self._save(observer)
        self._observer = observer
        return observer
