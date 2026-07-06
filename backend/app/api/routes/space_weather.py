"""NOAA SWPC space weather (Kp index, aurora forecast) -- read-only,
always served from cache (see `services/noaa_swpc.py`'s
`SpaceWeatherService`; a background loop in `main.py` is the only
thing that ever calls out to NOAA).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_space_weather_service
from app.core.exceptions import NotFoundError
from app.db.models.user import User
from app.schemas.common import ok
from app.services.noaa_swpc import SpaceWeatherService

router = APIRouter(prefix="/api/space-weather", tags=["space-weather"])


@router.get("/kp-index")
async def get_kp_index(
    service: SpaceWeatherService = Depends(get_space_weather_service),
    _: User = Depends(get_current_user),
) -> dict:
    """404s only until the very first background refresh completes
    (moments after startup) -- after that, always returns the last
    known data even if NOAA is currently unreachable."""
    kp = service.get_kp()
    if kp is None:
        raise NotFoundError("Kp index not yet available -- the first background refresh hasn't completed.")
    return ok(kp)


@router.get("/aurora.png")
async def get_aurora_png(
    service: SpaceWeatherService = Depends(get_space_weather_service),
    _: User = Depends(get_current_user),
) -> Response:
    png_bytes = service.get_aurora_png()
    if png_bytes is None:
        raise NotFoundError(
            "Aurora forecast not yet available -- the first background refresh hasn't completed."
        )
    return Response(content=png_bytes, media_type="image/png")


@router.get("/aurora/meta")
async def get_aurora_meta(
    service: SpaceWeatherService = Depends(get_space_weather_service),
    _: User = Depends(get_current_user),
) -> dict:
    meta = service.get_aurora_meta()
    if meta is None:
        raise NotFoundError(
            "Aurora forecast not yet available -- the first background refresh hasn't completed."
        )
    return ok(meta)


@router.get("/xray-flux")
async def get_xray_flux(
    service: SpaceWeatherService = Depends(get_space_weather_service),
    _: User = Depends(get_current_user),
) -> dict:
    xray = service.get_xray()
    if xray is None:
        raise NotFoundError(
            "X-ray flux not yet available -- the first background refresh hasn't completed."
        )
    return ok(xray)


@router.get("/solar-wind")
async def get_solar_wind(
    service: SpaceWeatherService = Depends(get_space_weather_service),
    _: User = Depends(get_current_user),
) -> dict:
    solar_wind = service.get_solar_wind()
    if solar_wind is None:
        raise NotFoundError(
            "Solar wind not yet available -- the first background refresh hasn't completed."
        )
    return ok(solar_wind)
