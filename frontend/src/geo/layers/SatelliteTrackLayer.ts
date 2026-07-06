import L from "leaflet";
import * as satellite from "satellite.js";
import type { MapLayer } from "../types";
import { registerLayer } from "../LayerRegistry";

const REFRESH_INTERVAL_MS = 5000;
const TRACK_WINDOW_MINUTES = 45; // each direction -- past and future
const TRACK_STEP_SECONDS = 30;

/**
 * Orbit calculations happen entirely client-side via `satellite.js`,
 * per the design goal of keeping the backend limited to distributing
 * TLE data (`GET /api/satellites/tle/{norad_id}`, already built) --
 * the backend never computes a position.
 *
 * Unlike `AprsStationsLayer`, this one has no data of its own until a
 * satellite is selected (there's no "current constellation" concept
 * yet) -- `setSatellite()` is the extra, layer-specific entry point
 * `GeospatialPage` calls from its own small satellite-picker control.
 * That's deliberately outside the `MapLayer` interface: the interface
 * only needs to cover what the *map* does with a layer (init/refresh/
 * enable/disable/destroy), not every layer's own configuration knobs.
 */
export class SatelliteTrackLayer implements MapLayer {
  readonly id = "satellite-track";
  readonly name = "Satellite Ground Track";
  readonly description = "Current position and ground track of a selected satellite (client-side SGP4).";
  readonly defaultEnabled = false;

  private map: L.Map | null = null;
  private group = L.layerGroup();
  private enabled = false;
  private timer: ReturnType<typeof setInterval> | null = null;
  private satrec: satellite.SatRec | null = null;
  private label = "";

  initialize(map: L.Map): void {
    this.map = map;
    this.timer = setInterval(() => void this.refresh(), REFRESH_INTERVAL_MS);
  }

  setSatellite(name: string, tleLine1: string, tleLine2: string): void {
    this.satrec = satellite.twoline2satrec(tleLine1, tleLine2);
    this.label = name;
    void this.refresh();
  }

  clearSatellite(): void {
    this.satrec = null;
    this.group.clearLayers();
  }

  refresh(): void {
    if (!this.satrec) return;
    this.group.clearLayers();

    const now = new Date();
    const current = this.positionAt(now);
    if (current) {
      const marker = L.circleMarker([current.lat, current.lon], {
        radius: 6,
        color: "#facc15",
        fillColor: "#facc15",
        fillOpacity: 0.9,
        weight: 2,
      });
      marker.bindPopup(`<strong>${this.label}</strong><br/>alt ${current.altitudeKm.toFixed(0)} km`);
      marker.addTo(this.group);
    }

    const track = this.groundTrack(now);
    for (const segment of track) {
      L.polyline(segment, { color: "#facc15", weight: 1.5, opacity: 0.6, dashArray: "4 4" }).addTo(this.group);
    }
  }

  private positionAt(when: Date): { lat: number; lon: number; altitudeKm: number } | null {
    if (!this.satrec) return null;
    const result = satellite.propagate(this.satrec, when);
    if (!result || !result.position) return null; // SGP4 propagation error (e.g. decayed orbit)

    const gmst = satellite.gstime(when);
    const geo = satellite.eciToGeodetic(result.position, gmst);
    return {
      lat: satellite.degreesLat(geo.latitude),
      lon: satellite.degreesLong(geo.longitude),
      altitudeKm: geo.height,
    };
  }

  /** Splits into multiple segments at the antimeridian so a pass that
   * crosses +-180deg longitude doesn't draw one line straight across
   * the map. */
  private groundTrack(now: Date): Array<[number, number][]> {
    const segments: Array<[number, number][]> = [];
    let current: [number, number][] = [];
    let previousLon: number | null = null;

    const startMs = now.getTime() - TRACK_WINDOW_MINUTES * 60_000;
    const endMs = now.getTime() + TRACK_WINDOW_MINUTES * 60_000;
    for (let t = startMs; t <= endMs; t += TRACK_STEP_SECONDS * 1000) {
      const point = this.positionAt(new Date(t));
      if (!point) continue;

      // A real antimeridian crossing has consecutive longitudes on
      // opposite sides of +-180deg with both close to it (e.g. +179.5
      // then -179.5). A simple "|delta| > 180" check also fires
      // falsely near-polar passes: satellite.js's eciToGeodetic always
      // returns longitude wrapped to [-180, 180], but right over a
      // pole the sub-satellite longitude is nearly undefined and can
      // swing wildly between samples even though the ground track
      // barely moved -- that's not a real date-line crossing, and
      // splitting the line there (rather than at the actual seam)
      // is exactly the spurious gap a near-polar orbit like NOAA 15's
      // (98.5deg inclination) would otherwise produce every pass.
      const crossedAntimeridian =
        previousLon !== null &&
        Math.sign(point.lon) !== Math.sign(previousLon) &&
        Math.abs(point.lon) > 170 &&
        Math.abs(previousLon) > 170;
      if (crossedAntimeridian) {
        if (current.length > 1) segments.push(current);
        current = [];
      }
      current.push([point.lat, point.lon]);
      previousLon = point.lon;
    }
    if (current.length > 1) segments.push(current);
    return segments;
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

registerLayer(() => new SatelliteTrackLayer());
