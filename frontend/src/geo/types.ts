import type * as L from "leaflet";

/**
 * Common interface every map layer implements -- the map/page never
 * knows a layer's implementation details (what it fetches, how often
 * it redraws, whether it's backed by Echo Base's own API or a raw
 * client-side computation like satellite ground tracks). Adding a new
 * layer means writing a class that satisfies this interface and
 * registering it (see LayerRegistry.ts) -- nothing else in the map
 * page changes.
 */
export interface MapLayer {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  /** Whether this layer is turned on the first time the map loads. */
  readonly defaultEnabled: boolean;

  /** Called once, when the layer is first registered with a live map instance. */
  initialize(map: L.Map): void | Promise<void>;
  /** Re-fetch/recompute and redraw. Safe to call whether enabled or not. */
  refresh(): void | Promise<void>;
  /** Add this layer's Leaflet objects to the map. */
  enable(): void;
  /** Remove this layer's Leaflet objects from the map (state is kept, not destroyed). */
  disable(): void;
  /** Tear down entirely -- timers, subscriptions, everything. Called on unmount. */
  destroy(): void;
}

export type LayerFactory = () => MapLayer;
