"""Fetches a satellite's current TLE from n2yo.com's free (registration
required) API, so the Satellites page doesn't require pasting TLE text
by hand for every lookup -- see `satellite_passes.py`'s docstring for
why nothing is cached/bundled here either: a TLE fetched today is
exactly as stale in a week as one typed in by hand would be, this just
automates *getting* a current one, not storing it.
"""
from __future__ import annotations

import httpx

N2YO_BASE_URL = "https://api.n2yo.com/rest/v1/satellite"


class N2yoError(Exception):
    pass


async def fetch_tle(norad_id: int, api_key: str) -> tuple[str, str, str]:
    """Returns (name, tle_line1, tle_line2). Raises N2yoError on any
    failure -- missing/invalid key, unknown NORAD id, network error,
    or a response that doesn't actually contain a TLE (n2yo returns
    HTTP 200 with an empty/malformed body for some bad requests rather
    than a clean error status)."""
    url = f"{N2YO_BASE_URL}/tle/{norad_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params={"apiKey": api_key})
    except httpx.HTTPError as exc:
        raise N2yoError(f"Could not reach n2yo.com: {exc}") from exc

    if response.status_code != 200:
        raise N2yoError(f"n2yo.com returned HTTP {response.status_code}.")

    try:
        body = response.json()
    except ValueError as exc:
        raise N2yoError("n2yo.com returned a non-JSON response.") from exc

    info = body.get("info", {})
    if info.get("transactionscount") == 0 and "tle" not in body:
        raise N2yoError(f"Unknown NORAD catalog number: {norad_id}.")

    raw_tle = body.get("tle")
    if not raw_tle or "\r\n" not in raw_tle:
        raise N2yoError("n2yo.com response did not include a usable TLE.")

    tle_line1, tle_line2 = raw_tle.split("\r\n", 1)
    name = info.get("satname", str(norad_id))
    return name, tle_line1.strip(), tle_line2.strip()
