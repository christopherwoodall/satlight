import dataclasses
import json
from datetime import UTC, datetime, timedelta

import httpx
import respx
from helpers import gp_row

from satlight.services.catalog import (
    load_catalog,
    maybe_refresh_catalog,
    should_refresh,
)


def test_load_rejects_stale_epoch(fresh_catalog):
    records = load_catalog(fresh_catalog)
    norads = {r.sat_id for r in records}
    assert 44713 in norads  # fresh starlink
    assert 25544 in norads  # fresh iss
    assert 900 not in norads  # stale junk dropped
    assert {r.type for r in records} == {"STARLINK", "ISS"}


def test_fresh_cache_blocks_refresh(fresh_catalog):
    assert should_refresh(fresh_catalog) is False


def test_cooldown_blocks_refresh(cfg):
    # No cache file -> would normally refresh, but cooldown is active.
    future = (datetime.now(UTC) + timedelta(hours=5)).isoformat()
    cfg.fetch_state_path.write_text(json.dumps({"cooldown_until": future}))
    assert should_refresh(cfg) is False


def test_min_interval_blocks_refresh(cfg):
    recent = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    cfg.fetch_state_path.write_text(json.dumps({"last_attempt": recent}))
    assert should_refresh(cfg) is False


def test_disabled_refresh_blocks_refresh(cfg):
    disabled_cfg = dataclasses.replace(cfg, disable_catalog_refresh=True)
    assert should_refresh(disabled_cfg) is False


@respx.mock
async def test_refresh_downloads_and_clears_cooldown(cfg):
    now = datetime.now(UTC)
    body = "\n".join(
        [
            "OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,"
            "RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,"
            "CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,"
            "MEAN_MOTION_DOT,MEAN_MOTION_DDOT",
            gp_row("STARLINK-1", 12345, now),
        ]
    )
    respx.get(cfg.csv_url).mock(return_value=httpx.Response(200, text=body))

    assert await maybe_refresh_catalog(cfg) is True
    assert cfg.csv_cache_path.exists()
    state = json.loads(cfg.fetch_state_path.read_text())
    assert "last_success" in state
    assert "cooldown_until" not in state


@respx.mock
async def test_disabled_refresh_skips_download(cfg):
    disabled_cfg = dataclasses.replace(cfg, disable_catalog_refresh=True)
    route = respx.get(disabled_cfg.csv_url).mock(
        return_value=httpx.Response(200, text="OBJECT_NAME\n")
    )

    assert await maybe_refresh_catalog(disabled_cfg) is False
    assert route.called is False
    assert disabled_cfg.fetch_state_path.exists() is False


@respx.mock
async def test_blocked_sets_long_cooldown(cfg):
    respx.get(cfg.csv_url).mock(return_value=httpx.Response(403, text="banned"))

    assert await maybe_refresh_catalog(cfg) is False
    state = json.loads(cfg.fetch_state_path.read_text())
    cooldown = datetime.fromisoformat(state["cooldown_until"])
    assert cooldown > datetime.now(UTC) + timedelta(hours=12)
