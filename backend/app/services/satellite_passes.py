"""Satellite pass prediction (Phase 9: Satellite -- Pass prediction).

Propagates a satellite's orbit from a TLE (two-line element set) using
`sgp4` -- the actual industry-standard propagator (used by
NORAD/Celestrak/every real tracking tool), not something worth
re-deriving by hand -- and finds when it rises above/sets below a
minimum elevation for a given ground station, by sampling forward in
time at a fixed step and reporting each contiguous above-threshold
span as one pass.

Coordinate math (TEME -> ECEF -> topocentric az/el) uses a spherical-
Earth model and GMST-only TEME->ECEF rotation (no polar motion or
precession/nutation corrections) -- accurate enough for pass timing to
within roughly a minute, not survey-grade geodesy. This is the same
"simplified model with a documented, deliberate accuracy tradeoff"
approach `dsp.py`'s boxcar decimation already takes.

TLEs go stale (a satellite's orbital elements drift and need
re-fetching periodically, typically every 1-2 weeks for LEO
satellites like NOAA's polar orbiters) -- this module doesn't fetch,
cache, or ship any TLE data of its own. Callers must supply a current
TLE with each request (e.g. fetched from Celestrak); there's no
built-in fallback, since a bundled TLE would be stale (and silently
wrong) the moment it was written down here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sgp4.api import Satrec, jday

EARTH_RADIUS_KM = 6378.137


class InvalidTleError(ValueError):
    pass


def _tle_checksum_valid(line: str) -> bool:
    """TLE lines end in a mod-10 checksum digit over every other
    character (digits count as themselves, '-' counts as 1, everything
    else -- letters, spaces, '.', '+' -- counts as 0). `sgp4` itself
    doesn't validate this (it'll happily parse garbage into a
    zeroed-out orbit rather than raising), so this is the actual
    "is this a real TLE line" check."""
    if len(line) != 69:
        return False
    body, checksum = line[:-1], line[-1]
    if not checksum.isdigit():
        return False
    total = sum(int(ch) if ch.isdigit() else (1 if ch == "-" else 0) for ch in body)
    return total % 10 == int(checksum)


def _validate_tle(tle_line1: str, tle_line2: str) -> None:
    if not _tle_checksum_valid(tle_line1) or not tle_line1.startswith("1 "):
        raise InvalidTleError("TLE line 1 failed checksum/format validation.")
    if not _tle_checksum_valid(tle_line2) or not tle_line2.startswith("2 "):
        raise InvalidTleError("TLE line 2 failed checksum/format validation.")


@dataclass
class SatellitePass:
    aos_at: datetime  # acquisition of signal (rise above min_elevation_deg)
    los_at: datetime  # loss of signal (set below min_elevation_deg)
    max_elevation_deg: float


def _gmst_radians(when: datetime) -> float:
    """Greenwich Mean Sidereal Time, in radians -- how far the Earth has
    rotated since the J2000.0 epoch, needed to rotate a TEME-frame
    satellite position (inertial, doesn't rotate with the Earth) into
    ECEF (rotates with the Earth, what a ground station's lat/lon is
    fixed in)."""
    jd = _julian_date(when)
    t = (jd - 2451545.0) / 36525.0
    gmst_deg = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * t * t
        - t * t * t / 38710000.0
    )
    return math.radians(gmst_deg % 360.0)


def _julian_date(when: datetime) -> float:
    when = when.astimezone(UTC)
    year, month = when.year, when.month
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    day_fraction = (when.hour + when.minute / 60 + when.second / 3600) / 24
    return (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + when.day
        + day_fraction
        + b
        - 1524.5
    )


def _teme_to_ecef(x: float, y: float, z: float, when: datetime) -> tuple[float, float, float]:
    theta = _gmst_radians(when)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    return (cos_t * x + sin_t * y, -sin_t * x + cos_t * y, z)


def _observer_ecef(
    latitude_deg: float, longitude_deg: float, elevation_m: float
) -> tuple[float, float, float]:
    lat, lon = math.radians(latitude_deg), math.radians(longitude_deg)
    r = EARTH_RADIUS_KM + elevation_m / 1000.0
    return (r * math.cos(lat) * math.cos(lon), r * math.cos(lat) * math.sin(lon), r * math.sin(lat))


def _topocentric_elevation_deg(
    sat_ecef: tuple[float, float, float],
    latitude_deg: float,
    longitude_deg: float,
    elevation_m: float,
) -> float:
    """Elevation angle (degrees above the local horizon) of an ECEF
    point as seen from an observer at the given lat/lon/elevation --
    pure geometry, independent of SGP4, so it's directly testable with
    synthetic positions (e.g. "a point straight up should read ~90 deg")
    rather than only through a full TLE propagation."""
    sat_x, sat_y, sat_z = sat_ecef
    obs_x, obs_y, obs_z = _observer_ecef(latitude_deg, longitude_deg, elevation_m)
    dx, dy, dz = sat_x - obs_x, sat_y - obs_y, sat_z - obs_z

    lat, lon = math.radians(latitude_deg), math.radians(longitude_deg)
    # Local East-North-Up frame at the observer.
    east = -math.sin(lon) * dx + math.cos(lon) * dy
    north = -math.sin(lat) * math.cos(lon) * dx - math.sin(lat) * math.sin(lon) * dy + math.cos(lat) * dz
    up = math.cos(lat) * math.cos(lon) * dx + math.cos(lat) * math.sin(lon) * dy + math.sin(lat) * dz

    horizontal_range = math.hypot(east, north)
    return math.degrees(math.atan2(up, horizontal_range))


def _elevation_deg(
    satrec: Satrec, when: datetime, latitude_deg: float, longitude_deg: float, elevation_m: float
) -> float:
    jd, fr = jday(
        when.year, when.month, when.day, when.hour, when.minute, when.second + when.microsecond / 1e6
    )
    error, position, _velocity = satrec.sgp4(jd, fr)
    if error != 0:
        return -90.0  # propagation error (e.g. decayed orbit) -- treat as "never visible"

    sat_ecef = _teme_to_ecef(*position, when)
    return _topocentric_elevation_deg(sat_ecef, latitude_deg, longitude_deg, elevation_m)


def find_passes(
    tle_line1: str,
    tle_line2: str,
    latitude_deg: float,
    longitude_deg: float,
    elevation_m: float,
    start_at: datetime,
    hours: float,
    min_elevation_deg: float,
    step_seconds: float = 30.0,
) -> list[SatellitePass]:
    """Samples elevation every `step_seconds` from `start_at` for
    `hours` and reports each contiguous span where it's above
    `min_elevation_deg` as one pass -- coarse (a pass could in
    principle be missed if it's much shorter than `step_seconds`, which
    doesn't happen for real LEO passes at the default 30s step), not
    bisection-refined to the exact second, since satellite pass timing
    doesn't need sub-step precision to be useful."""
    _validate_tle(tle_line1, tle_line2)
    satrec = Satrec.twoline2rv(tle_line1, tle_line2)

    passes: list[SatellitePass] = []
    in_pass = False
    pass_start: datetime | None = None
    pass_max_elevation = -90.0

    steps = int(hours * 3600 / step_seconds)
    for i in range(steps + 1):
        when = start_at + timedelta(seconds=i * step_seconds)
        elevation = _elevation_deg(satrec, when, latitude_deg, longitude_deg, elevation_m)

        if elevation >= min_elevation_deg:
            if not in_pass:
                in_pass = True
                pass_start = when
                pass_max_elevation = elevation
            else:
                pass_max_elevation = max(pass_max_elevation, elevation)
        elif in_pass:
            assert pass_start is not None
            passes.append(SatellitePass(aos_at=pass_start, los_at=when, max_elevation_deg=pass_max_elevation))
            in_pass = False

    return passes
