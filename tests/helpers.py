from __future__ import annotations

from datetime import datetime

HEADER = (
    "OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,"
    "RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,"
    "CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,"
    "MEAN_MOTION_DOT,MEAN_MOTION_DDOT"
)


def gp_row(name: str, norad: int, epoch: datetime, *, mm: str = "15.5") -> str:
    iso = epoch.strftime("%Y-%m-%dT%H:%M:%S.%f")
    return (
        f"{name},2024-001A,{iso},{mm},.0001,51.6,100.0,100.0,100.0,0,U,"
        f"{norad},999,1000,.0001,.0,0"
    )


def write_catalog_csv(path, rows: list[str]) -> None:
    path.write_text("\n".join([HEADER, *rows]) + "\n")
