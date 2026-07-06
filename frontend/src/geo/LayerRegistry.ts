import type { LayerFactory } from "./types";

/**
 * Layers register themselves (see layers/index.ts, which just imports
 * every layer module -- each module calls `registerLayer` at import
 * time) rather than the map page importing and wiring up each layer
 * class by name. Adding a new layer is: write the class, add one
 * import line to layers/index.ts, done -- the page/map code above
 * this never needs to change.
 */
const factories: LayerFactory[] = [];

export function registerLayer(factory: LayerFactory): void {
  factories.push(factory);
}

export function createRegisteredLayers() {
  return factories.map((factory) => factory());
}
