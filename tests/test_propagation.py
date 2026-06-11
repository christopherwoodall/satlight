from satlight.projection_modes import list_modes
from satlight.services.catalog import load_catalog
from satlight.services.observer import Observer
from satlight.services.propagation import PropagationEngine


def test_frame_shapes_and_keys(fresh_catalog):
    records = load_catalog(fresh_catalog)
    engine = PropagationEngine(fresh_catalog, records)
    frame = engine.frame(Observer(36.16, -86.78, 243.0))

    n = len(records)
    assert frame["count"] == n
    for key in ("az", "alt", "next_az", "next_alt", "sunlit", "visible"):
        assert len(frame[key]) == n
    assert len(frame["track_az"][0]) == 3
    assert all(0.0 <= a < 360.0 for a in frame["az"])
    assert all(v in (0, 1) for v in frame["visible"])


def test_catalog_message_is_index_aligned(fresh_catalog):
    records = load_catalog(fresh_catalog)
    engine = PropagationEngine(fresh_catalog, records)
    cat = engine.catalog()
    assert cat["count"] == len(records)
    assert len(cat["ids"]) == len(cat["names"]) == len(cat["types"]) == len(records)


def test_empty_catalog_returns_empty_frame(cfg):
    engine = PropagationEngine(cfg, [])
    frame = engine.frame(Observer(0.0, 0.0, 0.0))
    assert frame["count"] == 0


def test_projection_modes_registered():
    modes = {m["id"]: m for m in list_modes()}
    assert "ceiling" in modes and "full_sky" in modes
    assert "stereographic" in modes
    assert modes["ceiling"]["default"] is True


def test_ground_point_is_reasonable(fresh_catalog):
    records = load_catalog(fresh_catalog)
    engine = PropagationEngine(fresh_catalog, records)
    point = engine.ground_point(records[0].sat_id)
    assert point is not None
    lat, lon = point
    assert -90.0 <= lat <= 90.0
    assert -180.0 <= lon <= 180.0


def test_ground_point_unknown_id(fresh_catalog):
    engine = PropagationEngine(fresh_catalog, load_catalog(fresh_catalog))
    assert engine.ground_point(999999999) is None
