import json

from satlight.services.cities import CityIndex


def _index(tmp_path):
    data = [
        {"name": "Tokyo", "country": "Japan", "cc": "JP", "lat": 35.69, "lon": 139.69},
        {"name": "London", "country": "UK", "cc": "GB", "lat": 51.51, "lon": -0.13},
        {
            "name": "Quito",
            "country": "Ecuador",
            "cc": "EC",
            "lat": -0.22,
            "lon": -78.51,
        },
    ]
    path = tmp_path / "cities.json"
    path.write_text(json.dumps(data))
    return CityIndex.load(path)


def test_nearest_picks_closest(tmp_path):
    idx = _index(tmp_path)
    assert idx.nearest(35.7, 139.7).name == "Tokyo"
    assert idx.nearest(51.0, 0.0).name == "London"
    assert idx.nearest(0.0, -78.0).name == "Quito"


def test_empty_index_returns_none(tmp_path):
    empty = CityIndex.load(tmp_path / "missing.json")
    assert empty.nearest(0.0, 0.0) is None
