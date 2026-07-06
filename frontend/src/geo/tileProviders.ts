/**
 * Base map tile sources -- swappable without touching GeospatialPage
 * or any layer. Both entries here are free, OSM-derived, and need no
 * API key/account (a deliberate constraint, not just what happened to
 * be convenient): CartoDB's tiles are still rendered from OpenStreetMap
 * data, just with a dark colorway, so switching between them is a
 * pure style choice, not a different data source.
 *
 * Adding a provider that needs an API key (e.g. a commercial tile
 * host) later just means adding another entry here with its own
 * `url`/`attribution`/`maxZoom` -- nothing else changes.
 */
export interface TileProvider {
  id: string;
  name: string;
  url: string;
  attribution: string;
  maxZoom: number;
}

export const TILE_PROVIDERS: TileProvider[] = [
  {
    id: "carto-dark",
    name: "Dark (CartoDB)",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    maxZoom: 20,
  },
  {
    id: "osm-standard",
    name: "OpenStreetMap (Standard)",
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  },
];

export const DEFAULT_TILE_PROVIDER_ID = "carto-dark";
