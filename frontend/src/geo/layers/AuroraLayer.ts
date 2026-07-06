import L from "leaflet";
import { AURORA_PNG_PATH, getAuroraMeta } from "../../api/spaceWeather";
import type { MapLayer } from "../types";
import { registerLayer } from "../LayerRegistry";

const POLL_INTERVAL_MS = 60000;
// The whole world, matching the equirectangular PNG
// services/noaa_swpc.py renders (column 0 = -180deg, row 0 = +90deg).
const WORLD_BOUNDS: L.LatLngBoundsExpression = [
  [-90, -180],
  [90, 180],
];

/**
 * Real data: NOAA SWPC's OVATION aurora forecast, rendered server-side
 * into a single transparent PNG (`GET /api/space-weather/aurora.png`)
 * rather than shipped as ~65k raw grid points -- see
 * `services/noaa_swpc.py`'s docstring for why. One `L.imageOverlay`
 * instead of thousands of markers.
 */
class AuroraLayer implements MapLayer {
  readonly id = "aurora";
  readonly name = "Aurora Forecast";
  readonly description = "NOAA SWPC OVATION aurora visibility forecast.";
  readonly defaultEnabled = false;

  private map: L.Map | null = null;
  private overlay: L.ImageOverlay | null = null;
  private enabled = false;
  private timer: ReturnType<typeof setInterval> | null = null;

  initialize(map: L.Map): void {
    this.map = map;
    this.overlay = L.imageOverlay(this.cacheBustedUrl(), WORLD_BOUNDS, { opacity: 0.65 });
    this.timer = setInterval(() => void this.refresh(), POLL_INTERVAL_MS);
    void this.refresh();
  }

  private cacheBustedUrl(): string {
    // The PNG is served from a cache that only actually changes every
    // few minutes server-side (see SpaceWeatherSettings), but browsers
    // will otherwise cache the image response indefinitely against
    // the unchanging URL -- a timestamp query param forces a real
    // re-fetch each poll.
    return `${AURORA_PNG_PATH}?t=${Date.now()}`;
  }

  async refresh(): Promise<void> {
    try {
      await getAuroraMeta(); // confirms data actually exists before swapping the image in
    } catch {
      return; // not available yet (still warming up, or NOAA's been unreachable since startup)
    }
    this.overlay?.setUrl(this.cacheBustedUrl());
  }

  enable(): void {
    if (this.enabled || !this.map || !this.overlay) return;
    this.enabled = true;
    this.overlay.addTo(this.map);
  }

  disable(): void {
    this.enabled = false;
    this.overlay?.remove();
  }

  destroy(): void {
    if (this.timer) clearInterval(this.timer);
    this.overlay?.remove();
  }
}

registerLayer(() => new AuroraLayer());
