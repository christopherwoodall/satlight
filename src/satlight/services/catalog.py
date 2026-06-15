"""Satellite catalog: local CSV cache + heavily rate-limited refresh.

Network policy (celestrak bans aggressive clients):
  * A fresh cache means zero network calls.
  * A refresh is only attempted when the cache is older than
    ``cache_max_age_hours`` AND the last attempt was more than
    ``min_fetch_interval_hours`` ago AND we are not inside a failure cooldown.
  * 403/429 responses trigger a long ``blocked_cooldown_hours`` backoff.
  * Any failure leaves the existing cache untouched; SatLight keeps running.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sgp4 import omm
from sgp4.api import Satrec, jday

from ..config import Config
from ..satellite_classifiers import classify


@dataclass(slots=True)
class SatelliteRecord:
    sat_id: int
    name: str
    type: str
    satrec: Satrec


def _now() -> datetime:
    return datetime.now(UTC)


def _read_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(path)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _cache_age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, UTC)
    return (_now() - mtime).total_seconds() / 3600.0


def should_refresh(cfg: Config, *, now: datetime | None = None) -> bool:
    """Decide whether a refresh attempt is permitted right now."""
    if cfg.disable_catalog_refresh:
        return False

    now = now or _now()
    state = _read_state(cfg.fetch_state_path)

    cooldown_until = _parse_dt(state.get("cooldown_until"))
    if cooldown_until and now < cooldown_until:
        return False

    age = _cache_age_hours(cfg.csv_cache_path)
    if age is not None and age < cfg.cache_max_age_hours:
        return False

    last_attempt = _parse_dt(state.get("last_attempt"))
    return not (
        last_attempt
        and (now - last_attempt) < timedelta(hours=cfg.min_fetch_interval_hours)
    )


async def maybe_refresh_catalog(cfg: Config) -> bool:
    """Refresh the cached CSV if policy allows. Returns True on a fresh download."""
    if not should_refresh(cfg):
        return False

    now = _now()
    state = _read_state(cfg.fetch_state_path)
    state["last_attempt"] = now.isoformat()
    _write_state(cfg.fetch_state_path, state)

    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": cfg.user_agent},
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            response = await client.get(cfg.csv_url)
    except httpx.HTTPError:
        state["cooldown_until"] = (
            now + timedelta(hours=cfg.failure_cooldown_hours)
        ).isoformat()
        _write_state(cfg.fetch_state_path, state)
        return False

    if response.status_code in (403, 429):
        state["cooldown_until"] = (
            now + timedelta(hours=cfg.blocked_cooldown_hours)
        ).isoformat()
        _write_state(cfg.fetch_state_path, state)
        return False

    if response.status_code != 200 or "OBJECT_NAME" not in response.text[:256]:
        state["cooldown_until"] = (
            now + timedelta(hours=cfg.failure_cooldown_hours)
        ).isoformat()
        _write_state(cfg.fetch_state_path, state)
        return False

    cfg.csv_cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cfg.csv_cache_path.with_suffix(".csv.tmp")
    tmp.write_text(response.text)
    tmp.replace(cfg.csv_cache_path)

    state["last_success"] = now.isoformat()
    state.pop("cooldown_until", None)
    _write_state(cfg.fetch_state_path, state)
    return True


def load_catalog(cfg: Config) -> list[SatelliteRecord]:
    """Parse the cached CSV into records, dropping stale-epoch satellites."""
    if not cfg.csv_cache_path.exists():
        return []

    now = _now()
    jd_now, fr_now = jday(
        now.year, now.month, now.day, now.hour, now.minute, now.second
    )
    epoch_now = jd_now + fr_now
    max_age_days = cfg.max_epoch_age_hours / 24.0

    records: list[SatelliteRecord] = []
    with cfg.csv_cache_path.open(encoding="utf-8") as handle:
        for fields in omm.parse_csv(handle):
            sat = Satrec()
            omm.initialize(sat, fields)

            age_days = epoch_now - (sat.jdsatepoch + sat.jdsatepochF)
            if age_days > max_age_days:
                continue

            name = (fields.get("OBJECT_NAME") or f"NORAD {sat.satnum}").strip()
            records.append(
                SatelliteRecord(
                    sat_id=sat.satnum,
                    name=name,
                    type=classify(name, sat.satnum),
                    satrec=sat,
                )
            )
            if len(records) >= cfg.max_satellites:
                break

    return records
