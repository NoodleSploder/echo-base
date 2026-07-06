import L from "leaflet";
import { listAprsStations } from "../../api/aprs";
import type { MapLayer } from "../types";
import { registerLayer } from "../LayerRegistry";

const POLL_INTERVAL_MS = 15000;

/**
 * Real data: `GET /api/aprs/stations` (persisted last-known position
 * per callsign -- see `aprs_stations.py`). Nothing to configure here;
 * this layer just shows whatever the backend has actually decoded.
 */
class AprsStationsLayer implements MapLayer {
  readonly id = "aprs-stations";
  readonly name = "APRS Stations";
  readonly description = "Last known position of decoded APRS stations.";
  readonly defaultEnabled = true;

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
    let stations;
    try {
      stations = await listAprsStations();
    } catch {
      return; // transient poll failure; keep showing the last good markers
    }

    this.group.clearLayers();
    for (const station of stations) {
      const marker = L.circleMarker([station.latitude, station.longitude], {
        radius: 5,
        color: "#38bdf8",
        fillColor: "#38bdf8",
        fillOpacity: 0.85,
        weight: 1,
      });
      marker.bindPopup(
        `<strong>${station.callsign}</strong><br/>${station.last_info}<br/>` +
          `<span style="opacity:0.7">last heard ${new Date(station.last_heard_at).toLocaleString()}</span>`,
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

registerLayer(() => new AprsStationsLayer());
