"""NOAA Space Weather Prediction Center (SWPC) provider adapter.

Free, no API key, no registration -- unlike n2yo.com, nothing here is
gated. Two datasets:

- **Planetary K-index** (`fetch_kp_index`): a simple time series,
  passed through close to as-is.
- **OVATION aurora forecast** (`fetch_aurora_grid` /
  `render_aurora_png`): a full 1deg x 1deg global grid (360 longitudes
  x 181 latitudes = 65,160 points) of aurora-visibility probability.
  That's too many points to reasonably ship to the browser as
  individual markers/polygons (thousands of DOM/canvas objects), so
  this renders the grid server-side into a single transparent PNG
  (`render_aurora_png`, a pure function -- no network -- so it's
  testable against a synthetic grid) that the frontend displays with
  one `L.imageOverlay`, the same way `services/n2yo.py` isolates its
  own external provider's quirks behind a clean interface.

`SpaceWeatherService` holds the last-successfully-fetched data in
memory and only ever replaces it on a *successful* refresh -- a
provider hiccup serves the last-known-good data rather than an error,
per the "graceful failure" requirement. Nothing here talks to NOAA
synchronously from a request handler; a background refresh loop
(wired in `main.py`, same shape as `HotplugMonitor`) is the only thing
that ever calls these fetch functions.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import numpy as np
from PIL import Image

logger = logging.getLogger("echo_base.noaa_swpc")

KP_INDEX_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
AURORA_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"

GRID_LON_COUNT = 360
GRID_LAT_COUNT = 181  # -90..90 inclusive
# Aurora probability is on a coarse 0-100ish scale (observed values are
# usually well under 100 even during real storms) -- this just needs to
# separate "definitely visible" from "faint" for the color ramp, not
# match NOAA's own scale exactly.
AURORA_ALPHA_SCALE = 6.0
AURORA_MIN_ALPHA = 20  # even a probability of 1 should be faintly visible, not invisible


class SwpcError(Exception):
    pass


async def fetch_kp_index() -> list[dict[str, object]]:
    """Returns the raw list of `{time_tag, Kp, a_running, station_count}`
    readings NOAA publishes (typically the last several days at 3-hour
    resolution) -- normalization beyond parsing JSON isn't needed, the
    upstream shape is already exactly what a client wants."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(KP_INDEX_URL)
    except httpx.HTTPError as exc:
        raise SwpcError(f"Could not reach NOAA SWPC (Kp index): {exc}") from exc

    if response.status_code != 200:
        raise SwpcError(f"NOAA SWPC Kp index returned HTTP {response.status_code}.")
    try:
        data = response.json()
    except ValueError as exc:
        raise SwpcError("NOAA SWPC Kp index returned a non-JSON response.") from exc
    if not isinstance(data, list) or not data:
        raise SwpcError("NOAA SWPC Kp index returned an empty/unexpected response.")
    return data


@dataclass
class AuroraGrid:
    observation_time: str
    forecast_time: str
    # (longitude 0..359, latitude -90..90, probability) triples, exactly
    # as NOAA publishes them -- `render_aurora_png` does the coordinate
    # remapping, not this fetch step.
    points: list[tuple[int, int, int]]


async def fetch_aurora_grid() -> AuroraGrid:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(AURORA_URL)
    except httpx.HTTPError as exc:
        raise SwpcError(f"Could not reach NOAA SWPC (aurora): {exc}") from exc

    if response.status_code != 200:
        raise SwpcError(f"NOAA SWPC aurora endpoint returned HTTP {response.status_code}.")
    try:
        data = response.json()
    except ValueError as exc:
        raise SwpcError("NOAA SWPC aurora endpoint returned a non-JSON response.") from exc

    coordinates = data.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise SwpcError("NOAA SWPC aurora response had no coordinate grid.")

    return AuroraGrid(
        observation_time=str(data.get("Observation Time", "")),
        forecast_time=str(data.get("Forecast Time", "")),
        points=[(int(lon), int(lat), int(prob)) for lon, lat, prob in coordinates],
    )


def render_aurora_png(grid: AuroraGrid) -> bytes:
    """Renders the aurora probability grid to a transparent RGBA PNG
    covering the whole world (-90..90 lat, -180..180 lon), suitable for
    a single `L.imageOverlay` -- pure function, no network, so it's
    testable against a small synthetic grid rather than needing a live
    NOAA response."""
    # [lat_index][lon_index], lat_index 0 = -90 (south), lon_index 0 = 0deg (Greenwich).
    probabilities = np.zeros((GRID_LAT_COUNT, GRID_LON_COUNT), dtype=np.uint8)
    for lon, lat, prob in grid.points:
        if 0 <= lon < GRID_LON_COUNT and -90 <= lat <= 90:
            probabilities[lat + 90, lon] = max(0, min(255, prob))

    # Shift so column 0 is longitude -180 (matching the [[-90,-180],[90,180]]
    # bounds the frontend's L.imageOverlay uses) instead of NOAA's own
    # 0..359 (Greenwich-first) ordering.
    shifted = np.roll(probabilities, shift=GRID_LON_COUNT // 2, axis=1)
    # Image row 0 is the top of the image (north, +90deg) by convention;
    # `shifted` currently has row 0 = south (-90deg), so flip vertically.
    shifted = np.flipud(shifted)

    alpha = np.where(
        shifted > 0,
        np.clip(shifted.astype(np.float32) * AURORA_ALPHA_SCALE + AURORA_MIN_ALPHA, 0, 255),
        0,
    ).astype(np.uint8)

    rgba = np.zeros((GRID_LAT_COUNT, GRID_LON_COUNT, 4), dtype=np.uint8)
    rgba[..., 0] = 60  # a faint characteristic aurora green, not pure/saturated
    rgba[..., 1] = 220
    rgba[..., 2] = 130
    rgba[..., 3] = alpha

    image = Image.fromarray(rgba, mode="RGBA")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class SpaceWeatherService:
    """Holds the last-successfully-fetched Kp/aurora data in memory --
    a refresh failure logs and leaves the previous data in place rather
    than clearing it, so a transient NOAA outage doesn't blank out a
    dashboard that was working a minute ago."""

    def __init__(self) -> None:
        self._kp_readings: list[dict[str, object]] | None = None
        self._kp_updated_at: datetime | None = None
        self._aurora_png: bytes | None = None
        self._aurora_meta: dict[str, str] | None = None
        self._aurora_updated_at: datetime | None = None

    async def refresh_kp(self) -> None:
        try:
            readings = await fetch_kp_index()
        except SwpcError:
            logger.exception("Kp index refresh failed; keeping last known data")
            return
        self._kp_readings = readings
        self._kp_updated_at = datetime.now(UTC)

    async def refresh_aurora(self) -> None:
        try:
            grid = await fetch_aurora_grid()
            png_bytes = render_aurora_png(grid)
        except SwpcError:
            logger.exception("Aurora forecast refresh failed; keeping last known data")
            return
        self._aurora_png = png_bytes
        self._aurora_meta = {"observation_time": grid.observation_time, "forecast_time": grid.forecast_time}
        self._aurora_updated_at = datetime.now(UTC)

    def get_kp(self) -> dict[str, object] | None:
        if self._kp_readings is None or self._kp_updated_at is None:
            return None
        return {"readings": self._kp_readings, "cached_at": self._kp_updated_at.isoformat()}

    def get_aurora_png(self) -> bytes | None:
        return self._aurora_png

    def get_aurora_meta(self) -> dict[str, object] | None:
        if self._aurora_meta is None or self._aurora_updated_at is None:
            return None
        return {**self._aurora_meta, "cached_at": self._aurora_updated_at.isoformat()}
