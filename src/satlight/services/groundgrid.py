"""Server-computed ground grid for the background map overlay.

For each coastline vertex in the bundled world GeoJSON, compute the topocentric
(azimuth, altitude) of the point on the celestial sphere directly above that
ground location, as seen from the current observer.  This is done by projecting
the geocentric unit vector through each ground point into the observer's ENU
frame -- the same technique used for star directions, which naturally handles
the horizon geometry correctly.

The result is a compact JSON array of rings with ``[az, alt]`` pairs and
``null`` sentinels for below-horizon gaps.  The frontend projects these through
the active projection plugin, guaranteeing continents and satellites share the
exact same coordinate space.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .observer import Observer

_DEG = np.pi / 180.0


def _geodetic_unit(lat: float, lon: float) -> np.ndarray:
    """Unit vector from Earth center through (lat, lon) on the ellipsoid."""
    lat_r = lat * _DEG
    lon_r = lon * _DEG
    return np.array(
        [np.cos(lat_r) * np.cos(lon_r), np.cos(lat_r) * np.sin(lon_r), np.sin(lat_r)]
    )


def _enu_basis(obs: Observer) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lat = obs.latitude * _DEG
    lon = obs.longitude * _DEG
    sl, cl = np.sin(lat), np.cos(lat)
    so, co = np.sin(lon), np.cos(lon)
    east = np.array([-so, co, 0.0])
    north = np.array([-sl * co, -sl * so, cl])
    up = np.array([cl * co, cl * so, sl])
    return east, north, up


def compute_ground_grid(geo_path: Path, observer: Observer) -> list[list[float | None]]:
    """Return a list of rings, each a flat ``[az, alt, az, alt, ...]`` list.

    Below-horizon vertices are replaced with ``None`` sentinels so the
    frontend can break the path there.
    """
    try:
        data = json.loads(geo_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []

    east, north, up = _enu_basis(observer)

    rings: list[list[float | None]] = []
    for feature in data.get("features", []):
        geom = feature.get("geometry")
        if not geom:
            continue
        coords_list: list[list[list[float]]] = []
        if geom["type"] == "Polygon":
            coords_list = geom["coordinates"]
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                coords_list.extend(poly)

        for ring in coords_list:
            flat: list[float | None] = []
            for pt in ring:
                lon, lat = pt[0], pt[1]
                uvec = _geodetic_unit(lat, lon)
                e = float(uvec @ east)
                n = float(uvec @ north)
                u = float(uvec @ up)
                az = float(np.degrees(np.arctan2(e, n)) % 360.0)
                alt = float(np.degrees(np.arctan2(u, np.hypot(e, n))))
                if alt < -2.0:
                    flat.extend([None, None])
                else:
                    flat.extend([round(az, 2), round(alt, 2)])
            if any(v is not None for v in flat):
                rings.append(flat)

    return rings
