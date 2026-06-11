"""Analytical Sun position and Earth-shadow (sunlit) test.

We deliberately avoid shipping or downloading a JPL ephemeris. For the purpose
of dimming satellites that enter Earth's shadow, a low-precision analytical Sun
direction (accurate to ~0.01 deg) combined with a cylindrical umbra model is
more than sufficient and keeps SatLight fully offline.
"""

from __future__ import annotations

import numpy as np

EARTH_RADIUS_KM = 6371.0
_DEG = np.pi / 180.0
_J2000 = 2451545.0


def sun_unit_vector_eci(jd: float, fr: float = 0.0) -> np.ndarray:
    """Geocentric unit vector pointing at the Sun, in an equatorial inertial frame.

    ``jd + fr`` is the Julian date (UTC is close enough to UT1 here). The output
    shares the same frame (TEME / true equator) as SGP4 satellite positions
    closely enough for shadow geometry.
    """
    n = (jd - _J2000) + fr
    mean_long = (280.460 + 0.9856474 * n) % 360.0
    mean_anom = ((357.528 + 0.9856003 * n) % 360.0) * _DEG
    ecl_long = (
        mean_long + 1.915 * np.sin(mean_anom) + 0.020 * np.sin(2.0 * mean_anom)
    ) * _DEG
    obliquity = (23.439 - 3.6e-7 * n) * _DEG

    return np.array(
        [
            np.cos(ecl_long),
            np.cos(obliquity) * np.sin(ecl_long),
            np.sin(obliquity) * np.sin(ecl_long),
        ]
    )


def is_sunlit(positions_km: np.ndarray, sun_unit: np.ndarray) -> np.ndarray:
    """Boolean mask: which geocentric positions are lit by the Sun.

    ``positions_km`` is an ``(N, 3)`` array in the same frame as ``sun_unit``.
    Uses a cylindrical shadow: a satellite is in shadow only if it is on the
    anti-sun side and its distance from the Earth-Sun axis is below Earth's
    radius.
    """
    proj = positions_km @ sun_unit
    perp_sq = np.einsum("ij,ij->i", positions_km, positions_km) - proj * proj
    in_shadow = (proj < 0.0) & (perp_sq < EARTH_RADIUS_KM * EARTH_RADIUS_KM)
    return ~in_shadow
