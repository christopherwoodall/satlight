from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest
from helpers import gp_row, write_catalog_csv

from satlight.config import Config


@pytest.fixture
def cfg(tmp_path) -> Config:
    base = Config.load()
    return dataclasses.replace(
        base,
        cache_dir=tmp_path,
        csv_cache_path=tmp_path / "active.csv",
        fetch_state_path=tmp_path / "state.json",
        settings_path=tmp_path / "settings.json",
        max_satellites=100,
    )


@pytest.fixture
def fresh_catalog(cfg) -> Config:
    now = datetime.now(UTC)
    stale = now - timedelta(hours=200)
    write_catalog_csv(
        cfg.csv_cache_path,
        [
            gp_row("STARLINK-1007", 44713, now),
            gp_row("ISS (ZARYA)", 25544, now),
            gp_row("OLD JUNK", 900, stale),
        ],
    )
    return cfg
