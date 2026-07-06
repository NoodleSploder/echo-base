import L from "leaflet";
import { listAdsbAircraft } from "../../api/adsb";
import type { MapLayer } from "../types";
import { registerLayer } from "../LayerRegistry";

const POLL_INTERVAL_MS = 10000;

/**
 * Real data: `GET /api/adsb/aircraft`, filtered to aircraft with a
 * resolved position -- a Mode S message on its own often only carries
 * an ICAO address (identification-only), so position requires an
 * even/odd CPR frame pair (see `decoders/adsb_position.py`); not
 * every sighted aircraft will have one yet.
 */
class AdsbAircraftLayer implements MapLayer {
  readonly id = "adsb-aircraft";
  readonly name = "ADS-B Aircraft";
  readonly description = "Aircraft with a decoded position (Mode S/ADS-B, 1090MHz).";
  readonly defaultEnabled = false; // needs a wideband 1090MHz capture running to show anything

  private map: L.Map | null = null;
  private group = L.layerGroup();
  private enabled = false;
  private timer: ReturnType<typeof setInterval> | null = null;

  initialize(map: L.Map): void {
    this.map = map;
    this.timer = setInterval(() => void this.refresh(), POLL_INTERVAL_MS);
    void this.refresh();
  }

  async refresh(): Promise<void> {
    let aircraft;
    try {
      aircraft = await listAdsbAircraft();
    } catch {
      return; // transient poll failure; keep showing the last good markers
    }

    this.group.clearLayers();
    for (const plane of aircraft) {
      if (plane.latitude === null || plane.longitude === null) continue;
      const marker = L.circleMarker([plane.latitude, plane.longitude], {
        radius: 5,
        color: "#f472b6",
        fillColor: "#f472b6",
        fillOpacity: 0.85,
        weight: 1,
      });
      marker.bindPopup(
        `<strong>${plane.icao}</strong><br/>${plane.message_count} messages<br/>` +
          `<span style="opacity:0.7">last heard ${new Date(plane.last_seen_at).toLocaleString()}</span>`,
      );
      marker.addTo(this.group);
    }
  }

  enable(): void {
    if (this.enabled || !this.map) return;
    this.enabled = true;
    this.group.addTo(this.map);
  }

  disable(): void {
    this.enabled = false;
    this.group.remove();
  }

  destroy(): void {
    if (this.timer) clearInterval(this.timer);
    this.group.clearLayers();
    this.group.remove();
  }
}

registerLayer(() => new AdsbAircraftLayer());
