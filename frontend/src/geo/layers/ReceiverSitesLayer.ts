import L from "leaflet";
import { getReceiverInventory } from "../../api/receivers";
import type { MapLayer } from "../types";
import { registerLayer } from "../LayerRegistry";

const POLL_INTERVAL_MS = 30000;

/**
 * Real data: `GET /api/receivers/inventory`, filtered to receivers an
 * operator has actually placed on the map -- a plain RTL-SDR dongle has
 * no GPS of its own, so a location only ever exists once someone sets
 * one (see `PUT /api/receivers/{id}/location`). Unlike the other
 * layers, this one deliberately has nothing to show until that's done
 * at least once.
 */
class ReceiverSitesLayer implements MapLayer {
  readonly id = "receiver-sites";
  readonly name = "Receiver Sites";
  readonly description = "Physical location of receivers you've placed on the map.";
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
    let records;
    try {
      records = await getReceiverInventory();
    } catch {
      return; // transient poll failure; keep showing the last good markers
    }

    this.group.clearLayers();
    for (const record of records) {
      if (record.latitude === null || record.longitude === null) continue;
      const marker = L.circleMarker([record.latitude, record.longitude], {
        radius: 7,
        color: record.attached ? "#34d399" : "#64748b",
        fillColor: record.attached ? "#34d399" : "#64748b",
        fillOpacity: 0.85,
        weight: 2,
      });
      const label = record.site_name ?? record.name;
      marker.bindPopup(
        `<strong>${label}</strong><br/>${record.name} (${record.driver})<br/>` +
          `<span style="opacity:0.7">${record.attached ? "currently attached" : "not attached"} -- ` +
          `last seen ${new Date(record.last_seen_at).toLocaleString()}</span>`,
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

registerLayer(() => new ReceiverSitesLayer());
