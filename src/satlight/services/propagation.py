"""Vectorized orbital propagation.

All satellites are propagated together with a single :class:`SatrecArray` call
at five times per tick (now, now+velocity-sample, +5/+10/+15 min). Coordinate
transforms (TEME -> ECEF -> topocentric az/alt) are done with numpy, so the
engine scales to many thousands of satellites at 1 Hz.

The server computes everything the client needs; the client only renders.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
from sgp4.api import SatrecArray, jday

from ..config import Config
from .catalog import SatelliteRecord
from .observer import Observer
from .sun import is_sunlit, sun_unit_vector_eci

_DEG = np.pi / 180.0
_TWO_PI = 2.0 * np.pi

# WGS84
_WGS84_A_KM = 6378.137
_WGS84_E2 = 6.69437999014e-3

# Future-track sample offsets (seconds).
_TRACK_OFFSETS = (300.0, 600.0, 900.0)


def _gmst1982(jd: float, fr: float) -> float:
    """Greenwich Mean Sidereal Time (IAU-1982), radians, for TEME->ECEF."""
    t = ((jd - 2451545.0) + fr) / 36525.0
    seconds = (
        67310.54841
        + (876600.0 * 3600.0 + 8640184.812866) * t
        + 0.093104 * t * t
        - 6.2e-6 * t * t * t
    )
    return (seconds % 86400.0) * (_TWO_PI / 86400.0)


def _observer_ecef_km(obs: Observer) -> np.ndarray:
    lat = obs.latitude * _DEG
    lon = obs.longitude * _DEG
    h = obs.elevation_m / 1000.0
    sin_lat = np.sin(lat)
    n = _WGS84_A_KM / np.sqrt(1.0 - _WGS84_E2 * sin_lat * sin_lat)
    return np.array(
        [
            (n + h) * np.cos(lat) * np.cos(lon),
            (n + h) * np.cos(lat) * np.sin(lon),
            (n * (1.0 - _WGS84_E2) + h) * sin_lat,
        ]
    )


def _ecef_to_geodetic(x: float, y: float, z: float) -> tuple[float, float]:
    """ECEF (km) -> WGS84 geodetic (lat, lon) in degrees (Bowring's method)."""
    a = _WGS84_A_KM
    b = a * np.sqrt(1.0 - _WGS84_E2)
    ep2 = (a * a - b * b) / (b * b)
    p = np.hypot(x, y)
    th = np.arctan2(z * a, p * b)
    lat = np.arctan2(
        z + ep2 * b * np.sin(th) ** 3,
        p - _WGS84_E2 * a * np.cos(th) ** 3,
    )
    lon = np.arctan2(y, x)
    return float(np.degrees(lat)), float(np.degrees(lon))


def _enu_basis(obs: Observer) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lat = obs.latitude * _DEG
    lon = obs.longitude * _DEG
    sl, cl = np.sin(lat), np.cos(lat)
    so, co = np.sin(lon), np.cos(lon)
    east = np.array([-so, co, 0.0])
    north = np.array([-sl * co, -sl * so, cl])
    up = np.array([cl * co, cl * so, sl])
    return east, north, up


class PropagationEngine:
    def __init__(self, cfg: Config, records: list[SatelliteRecord]) -> None:
        self.cfg = cfg
        self.records = records
        self.ids = [r.sat_id for r in records]
        self.names = [r.name for r in records]
        self.types = [r.type for r in records]
        self._by_id = {r.sat_id: r for r in records}
        self._array = SatrecArray([r.satrec for r in records]) if records else None
        self._offsets = np.array([0.0, cfg.velocity_sample_seconds, *_TRACK_OFFSETS])

    def ground_point(self, norad_id: int) -> tuple[float, float] | None:
        """Sub-satellite geodetic (lat, lon) right now, for a single satellite."""
        record = self._by_id.get(norad_id)
        if record is None:
            return None

        now = datetime.now(UTC)
        jd, fr = jday(
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second + now.microsecond / 1e6,
        )
        err, teme, _ = record.satrec.sgp4(jd, fr)
        if err != 0:
            return None

        theta = _gmst1982(jd, fr)
        ct, st = np.cos(theta), np.sin(theta)
        xe = ct * teme[0] + st * teme[1]
        ye = -st * teme[0] + ct * teme[1]
        ze = teme[2]
        return _ecef_to_geodetic(xe, ye, ze)

    def catalog(self) -> dict:
        return {
            "type": "catalog",
            "count": len(self.records),
            "ids": self.ids,
            "names": self.names,
            "types": self.types,
        }

    def frame(self, observer: Observer) -> dict:
        now = datetime.now(UTC)
        if self._array is None:
            return {"type": "frame", "t": now.timestamp(), "count": 0}

        base_jd, base_fr = jday(
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second + now.microsecond / 1e6,
        )
        fr = base_fr + self._offsets / 86400.0
        jd = np.full(fr.shape, base_jd)

        errors, teme, _ = self._array.sgp4(jd, fr)  # teme: (n, 5, 3) km
        valid = errors[:, 0] == 0

        thetas = np.array([_gmst1982(base_jd, f) for f in fr])  # (5,)
        cos_t = np.cos(thetas)[None, :]
        sin_t = np.sin(thetas)[None, :]
        xt, yt, zt = teme[:, :, 0], teme[:, :, 1], teme[:, :, 2]
        xe = cos_t * xt + sin_t * yt
        ye = -sin_t * xt + cos_t * yt
        ze = zt

        obs_ecef = _observer_ecef_km(observer)
        east, north, up = _enu_basis(observer)
        dx = xe - obs_ecef[0]
        dy = ye - obs_ecef[1]
        dz = ze - obs_ecef[2]
        e = dx * east[0] + dy * east[1] + dz * east[2]
        n = dx * north[0] + dy * north[1] + dz * north[2]
        u = dx * up[0] + dy * up[1] + dz * up[2]

        az = np.degrees(np.arctan2(e, n)) % 360.0  # (n, 5)
        alt = np.degrees(np.arctan2(u, np.hypot(e, n)))  # (n, 5)

        az_now, alt_now = az[:, 0], alt[:, 0]
        az_next, alt_next = az[:, 1], alt[:, 1]

        dt = self.cfg.velocity_sample_seconds or 1.0
        d_az = (((az_next - az_now) + 180.0) % 360.0) - 180.0
        az_vel = d_az / dt
        alt_vel = (alt_next - alt_now) / dt

        sun_unit = sun_unit_vector_eci(base_jd, base_fr)
        sunlit = is_sunlit(teme[:, 0, :], sun_unit) & valid
        visible = (alt_now >= 0.0) & valid

        az_now = np.where(valid, az_now, 0.0)
        alt_now = np.where(valid, alt_now, -90.0)

        return {
            "type": "frame",
            "t": now.timestamp(),
            "interval": self.cfg.update_interval_seconds,
            "count": len(self.records),
            "az": np.round(az_now, 2).tolist(),
            "alt": np.round(alt_now, 2).tolist(),
            "az_velocity": np.round(az_vel, 3).tolist(),
            "alt_velocity": np.round(alt_vel, 3).tolist(),
            "next_az": np.round(az_next, 2).tolist(),
            "next_alt": np.round(alt_next, 2).tolist(),
            "sunlit": sunlit.astype(np.uint8).tolist(),
            "visible": visible.astype(np.uint8).tolist(),
            "track_az": np.round(az[:, 2:5], 1).tolist(),
            "track_alt": np.round(alt[:, 2:5], 1).tolist(),
        }
