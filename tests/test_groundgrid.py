from satlight.services.groundgrid import compute_ground_grid
from satlight.services.observer import Observer


def test_ground_grid_returns_rings(tmp_path):
    import json

    geo = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[-86.0, 36.0], [-86.0, 37.0], [-85.0, 37.0], [-86.0, 36.0]]
                    ],
                },
            }
        ],
    }
    path = tmp_path / "world.json"
    path.write_text(json.dumps(geo))

    obs = Observer(36.1627, -86.7816, 243.0)
    rings = compute_ground_grid(path, obs)
    assert len(rings) == 1
    # All 4 vertices should be above the horizon (they're near the observer).
    non_null = [v for v in rings[0] if v is not None]
    assert len(non_null) == 8  # 4 points * 2 values


def test_observer_zenith_in_grid(tmp_path):
    import json
    import numpy as np

    geo = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[-86.7816, 36.1627], [-86.0, 36.0], [-86.0, 37.0], [-86.7816, 36.1627]]
                    ],
                },
            }
        ],
    }
    path = tmp_path / "world.json"
    path.write_text(json.dumps(geo))

    obs = Observer(36.1627, -86.7816, 243.0)
    rings = compute_ground_grid(path, obs)
    # First vertex is the observer's own location -> should be near zenith (alt ~90).
    az, alt = rings[0][0], rings[0][1]
    assert alt > 89.0  # effectively at zenith


def test_empty_geojson_returns_empty(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text('{"type":"FeatureCollection","features":[]}')
    obs = Observer(0.0, 0.0, 0.0)
    assert compute_ground_grid(path, obs) == []


def test_missing_file_returns_empty(tmp_path):
    obs = Observer(0.0, 0.0, 0.0)
    assert compute_ground_grid(tmp_path / "missing.json", obs) == []
