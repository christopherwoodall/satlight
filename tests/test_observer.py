import json

from satlight.config import DEFAULT_OBSERVER_LATITUDE
from satlight.services.observer import ObserverStore


def test_seeds_defaults_and_writes_file(cfg):
    store = ObserverStore(cfg)
    assert store.current.latitude == DEFAULT_OBSERVER_LATITUDE
    assert cfg.settings_path.exists()


def test_update_persists_and_hot_reloads(cfg):
    store = ObserverStore(cfg)
    store.update(40.0, -74.0, 10.0)

    on_disk = json.loads(cfg.settings_path.read_text())
    assert on_disk["latitude"] == 40.0
    assert on_disk["longitude"] == -74.0

    # A fresh store reads the saved value (no restart needed in practice).
    assert ObserverStore(cfg).current.longitude == -74.0


def test_update_clamps_and_wraps(cfg):
    store = ObserverStore(cfg)
    obs = store.update(200.0, 540.0, 5.0)
    assert obs.latitude == 90.0
    assert -180.0 <= obs.longitude <= 180.0
