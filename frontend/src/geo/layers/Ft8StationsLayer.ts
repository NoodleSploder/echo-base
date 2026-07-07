import L from "leaflet";
import { listFt8Stations } from "../../api/ft8";
import type { MapLayer } from "../types";
import { registerLayer } from "../LayerRegistry";

const POLL_INTERVAL_MS = 15000;

/**
 * Real data: `GET /api/ft8/stations`, filtered to stations whose
 * decoded message happened to carry a grid locator (not every FT8
 * message does -- a signal report or token like "RR73" doesn't).
 * Position is the *grid square's centroid*, not a real GPS fix -- FT8
 * only ever conveys a 4-character Maidenhead locator (roughly
 * 150km x 300km at mid-latitudes), the same coarse resolution every
 * real FT8 spotting map (e.g. PSKReporter) shows.
 */
class Ft8StationsLayer implements MapLayer {
  readonly id = "ft8-stations";
  readonly name = "FT8 Stations";
  readonly description = "Decoded FT8 stations, positioned at their grid square's centroid.";
  readonly defaultEnabled = false; // needs an active HF/USB capture to show anything

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
      stations = await listFt8Stations();
    } catch {
      return; // transient poll failure; keep showing the last good markers
    }

    this.group.clearLayers();
    for (const station of stations) {
      if (station.latitude === null || station.longitude === null) continue;
      const marker = L.circleMarker([station.latitude, station.longitude], {
        radius: 5,
        color: "#facc15",
        fillColor: "#facc15",
        fillOpacity: 0.85,
        weight: 1,
      });
      marker.bindPopup(
        `<strong>${station.callsign}</strong> (${station.grid})<br/>${station.last_message}<br/>` +
          `<span style="opacity:0.7">${station.frequency_offset_hz.toFixed(0)}Hz -- ` +
          `${station.message_count} messages -- last heard ${new Date(station.last_heard_at).toLocaleString()}</span>`,
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

registerLayer(() => new Ft8StationsLayer());
