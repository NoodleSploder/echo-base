import L from "leaflet";
import { useEffect, useRef, useState } from "react";
import { fetchTleByNoradId } from "../api/satellites";
import { createRegisteredLayers } from "../geo/LayerRegistry";
import "../geo/layers"; // side-effect import: every layer module registers itself
import { SatelliteTrackLayer } from "../geo/layers/SatelliteTrackLayer";
import { DEFAULT_TILE_PROVIDER_ID, TILE_PROVIDERS } from "../geo/tileProviders";
import type { MapLayer } from "../geo/types";

const INITIAL_CENTER: [number, number] = [39.5, -98.35]; // continental US, a reasonable default
const INITIAL_ZOOM = 4;
const TILE_SIZE_PX = 256; // Leaflet/Web Mercator's standard tile size -- the whole world is TILE_SIZE_PX * 2^zoom px square

/** The lowest zoom at which one full world copy is at least as large
 * (in both dimensions) as the map container -- below this, Leaflet
 * has no choice but to tile multiple world copies side by side to
 * fill the visible area, which is the "chained maps" artifact rather
 * than a single continuously-wrapping world. Using the *larger* of
 * width/height (not just height) is what actually prevents that for
 * a wide-but-short container: a height-only constraint would let the
 * world end up much narrower than a wide container, which is exactly
 * the repeat-tiling problem, not a fix for it. */
function minZoomToFillContainer(widthPx: number, heightPx: number): number {
  const largestDimension = Math.max(widthPx, heightPx, 1);
  return Math.max(0, Math.ceil(Math.log2(largestDimension / TILE_SIZE_PX)));
}

// Full-screen Leaflet map hosting every registered layer (see
// geo/LayerRegistry.ts) -- this component only knows the common
// MapLayer interface, never a specific layer's implementation. See
// ARCHITECTURE.md's "Geospatial Intelligence Platform" section for
// the full design.
export function GeospatialPage() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const layersRef = useRef<MapLayer[]>([]);

  const [tileProviderId, setTileProviderId] = useState(DEFAULT_TILE_PROVIDER_ID);
  const [layerEnabled, setLayerEnabled] = useState<Record<string, boolean>>({});
  const [cursor, setCursor] = useState<{ lat: number; lon: number } | null>(null);

  const [noradId, setNoradId] = useState("");
  const [satelliteBusy, setSatelliteBusy] = useState(false);
  const [satelliteError, setSatelliteError] = useState<string | null>(null);
  const [trackedSatellite, setTrackedSatellite] = useState<string | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const container = mapContainerRef.current;
    const initialMinZoom = minZoomToFillContainer(container.clientWidth, container.clientHeight);

    const map = L.map(container, {
      zoomControl: true,
      // Panning past +-180deg longitude seamlessly continues from the
      // other side (a single circularly-wrapping world) instead of
      // drifting into unbounded coordinate space.
      worldCopyJump: true,
      minZoom: Math.max(INITIAL_ZOOM, initialMinZoom),
      // Latitude is clamped (Web Mercator can't sanely render past
      // ~85deg anyway); longitude is deliberately unbounded so the
      // circular wrap above isn't fighting a hard edge.
      maxBounds: L.latLngBounds([-85.06, -Infinity], [85.06, Infinity]),
      maxBoundsViscosity: 1.0,
    }).setView(INITIAL_CENTER, Math.max(INITIAL_ZOOM, initialMinZoom));
    L.control.scale({ imperial: false }).addTo(map);

    // The min-zoom-to-avoid-repeats calculation depends on container
    // size, which changes on window resize (this page is always
    // full-height, but width can change, e.g. a narrower browser
    // window) -- recompute and tighten the floor if needed.
    const handleResize = () => {
      const nextMinZoom = minZoomToFillContainer(container.clientWidth, container.clientHeight);
      map.setMinZoom(nextMinZoom);
    };
    window.addEventListener("resize", handleResize);
    map.on("mousemove", (event: L.LeafletMouseEvent) => {
      // Leaflet lets the map scroll continuously across repeated
      // "world copies" past +-180deg longitude (so panning feels
      // seamless) -- event.latlng.lng reflects that unwrapped
      // coordinate (e.g. -352 instead of 8), which is correct for
      // Leaflet's own purposes but not what a human wants to read.
      // wrap() normalizes it back to -180..180 for display only.
      const wrapped = event.latlng.wrap();
      setCursor({ lat: wrapped.lat, lon: wrapped.lng });
    });
    mapRef.current = map;

    const provider = TILE_PROVIDERS.find((p) => p.id === DEFAULT_TILE_PROVIDER_ID) ?? TILE_PROVIDERS[0];
    tileLayerRef.current = L.tileLayer(provider.url, {
      attribution: provider.attribution,
      maxZoom: provider.maxZoom,
    }).addTo(map);

    const layers = createRegisteredLayers();
    layersRef.current = layers;
    const initialEnabled: Record<string, boolean> = {};
    for (const layer of layers) {
      void layer.initialize(map);
      initialEnabled[layer.id] = layer.defaultEnabled;
      if (layer.defaultEnabled) layer.enable();
    }
    setLayerEnabled(initialEnabled);

    return () => {
      window.removeEventListener("resize", handleResize);
      for (const layer of layers) layer.destroy();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  function handleTileProviderChange(id: string) {
    setTileProviderId(id);
    const map = mapRef.current;
    const provider = TILE_PROVIDERS.find((p) => p.id === id);
    if (!map || !provider) return;
    tileLayerRef.current?.remove();
    tileLayerRef.current = L.tileLayer(provider.url, {
      attribution: provider.attribution,
      maxZoom: provider.maxZoom,
    }).addTo(map);
  }

  function toggleLayer(layer: MapLayer) {
    const nextEnabled = !layerEnabled[layer.id];
    setLayerEnabled((prev) => ({ ...prev, [layer.id]: nextEnabled }));
    if (nextEnabled) layer.enable();
    else layer.disable();
  }

  async function handleTrackSatellite() {
    const parsed = Number(noradId);
    if (!Number.isFinite(parsed) || parsed <= 0) return;
    setSatelliteBusy(true);
    setSatelliteError(null);
    try {
      const tle = await fetchTleByNoradId(parsed);
      const trackLayer = layersRef.current.find(
        (layer): layer is SatelliteTrackLayer => layer.id === "satellite-track",
      );
      trackLayer?.setSatellite(tle.name, tle.tle_line1, tle.tle_line2);
      if (trackLayer && !layerEnabled[trackLayer.id]) {
        trackLayer.enable();
        setLayerEnabled((prev) => ({ ...prev, [trackLayer.id]: true }));
      }
      setTrackedSatellite(tle.name);
    } catch {
      setSatelliteError("Could not fetch TLE -- check the NORAD ID or n2yo.com API key configuration.");
    } finally {
      setSatelliteBusy(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-3">
      <div className="w-64 shrink-0 space-y-3 overflow-y-auto rounded-lg border border-base-700 bg-base-900/60 p-3 text-sm">
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Base Map</h2>
          <select
            value={tileProviderId}
            onChange={(event) => handleTileProviderChange(event.target.value)}
            className="w-full rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-200"
          >
            {TILE_PROVIDERS.map((provider) => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Layers</h2>
          <ul className="space-y-1">
            {layersRef.current.map((layer) => (
              <li key={layer.id} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={layerEnabled[layer.id] ?? layer.defaultEnabled}
                  onChange={() => toggleLayer(layer)}
                  className="mt-0.5"
                />
                <div>
                  <div className="flex items-center gap-1.5 text-slate-200">
                    {layer.name}
                    {layerEnabled[layer.id] && (
                      <span
                        className="h-1.5 w-1.5 rounded-full bg-emerald-400"
                        title="Live -- auto-refreshing"
                      />
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500">{layer.description}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="border-t border-base-700 pt-3">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Track Satellite
          </h2>
          <div className="flex gap-1">
            <input
              type="number"
              value={noradId}
              onChange={(event) => setNoradId(event.target.value)}
              placeholder="NORAD ID"
              className="w-full rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-200 placeholder:text-slate-500"
            />
            <button
              type="button"
              onClick={() => void handleTrackSatellite()}
              disabled={satelliteBusy || !noradId}
              className="shrink-0 rounded-md border border-base-600 px-2 py-1 text-xs text-slate-300 hover:bg-base-800 disabled:opacity-50"
            >
              {satelliteBusy ? "..." : "Track"}
            </button>
          </div>
          {trackedSatellite && (
            <p className="mt-1 text-[11px] text-emerald-400">Tracking: {trackedSatellite}</p>
          )}
          {satelliteError && <p className="mt-1 text-[11px] text-red-400">{satelliteError}</p>}
        </div>

        <div className="border-t border-base-700 pt-3 text-[11px] text-slate-500">
          {cursor ? (
            <span>
              {cursor.lat.toFixed(4)}, {cursor.lon.toFixed(4)}
            </span>
          ) : (
            <span>Move the mouse over the map for coordinates</span>
          )}
        </div>
      </div>

      <div ref={mapContainerRef} className="min-w-0 flex-1 rounded-lg border border-base-700" />
    </div>
  );
}
