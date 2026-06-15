"""Static application configuration.

All values here are read once at startup from the environment (optionally via a
local ``.env`` file). Nothing in this module is mutated at runtime. The only
runtime-mutable state in SatLight is the observer location, which lives in
``settings.json`` and is owned by :mod:`satlight.services.observer`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Hardcoded observer defaults. These seed settings.json on first run; the file
# is the source of truth afterwards. (Nashville, TN.)
DEFAULT_OBSERVER_LATITUDE = 36.1627
DEFAULT_OBSERVER_LONGITUDE = -86.7816
DEFAULT_OBSERVER_ELEVATION_M = 243.0

DEFAULT_CSV_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv"
DEFAULT_USER_AGENT = "SatLight/0.1.0 (+https://local.satlight; contact=local-operator)"


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Config:
    host: str
    port: int

    update_interval_seconds: float
    velocity_sample_seconds: float

    csv_url: str
    user_agent: str
    disable_catalog_refresh: bool

    cache_dir: Path
    csv_cache_path: Path
    fetch_state_path: Path

    cache_max_age_hours: float
    min_fetch_interval_hours: float
    failure_cooldown_hours: float
    blocked_cooldown_hours: float

    max_epoch_age_hours: float
    max_satellites: int

    settings_path: Path

    @classmethod
    def load(cls) -> Config:
        load_dotenv()

        cache_dir = Path(os.getenv("SATLIGHT_CACHE_DIR", ".cache"))
        csv_cache_path = Path(
            os.getenv(
                "SATLIGHT_CSV_CACHE_PATH", str(cache_dir / "celestrak_active.csv")
            )
        )
        fetch_state_path = Path(
            os.getenv(
                "SATLIGHT_FETCH_STATE_PATH",
                str(cache_dir / "celestrak_fetch_state.json"),
            )
        )

        return cls(
            host=os.getenv("SATLIGHT_HOST", "127.0.0.1"),
            port=_env_int("SATLIGHT_PORT", 8000),
            update_interval_seconds=_env_float("SATLIGHT_UPDATE_INTERVAL_SECONDS", 1.0),
            velocity_sample_seconds=_env_float("SATLIGHT_VELOCITY_SAMPLE_SECONDS", 1.0),
            csv_url=os.getenv("SATLIGHT_CSV_URL", DEFAULT_CSV_URL),
            user_agent=os.getenv("SATLIGHT_USER_AGENT", DEFAULT_USER_AGENT),
            disable_catalog_refresh=_env_bool(
                "SATLIGHT_DISABLE_CATALOG_REFRESH", False
            ),
            cache_dir=cache_dir,
            csv_cache_path=csv_cache_path,
            fetch_state_path=fetch_state_path,
            cache_max_age_hours=_env_float("SATLIGHT_CACHE_MAX_AGE_HOURS", 12.0),
            min_fetch_interval_hours=_env_float(
                "SATLIGHT_MIN_FETCH_INTERVAL_HOURS", 2.0
            ),
            failure_cooldown_hours=_env_float("SATLIGHT_FAILURE_COOLDOWN_HOURS", 6.0),
            blocked_cooldown_hours=_env_float("SATLIGHT_BLOCKED_COOLDOWN_HOURS", 24.0),
            max_epoch_age_hours=_env_float("SATLIGHT_MAX_EPOCH_AGE_HOURS", 72.0),
            max_satellites=_env_int("SATLIGHT_MAX_SATELLITES", 2000),
            settings_path=Path(os.getenv("SATLIGHT_SETTINGS_PATH", "settings.json")),
        )
