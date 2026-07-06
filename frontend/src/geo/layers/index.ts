// Every layer module registers itself (calls `registerLayer` at
// import time -- see LayerRegistry.ts) as a side effect of being
// imported here. Adding a new layer is exactly one new import line;
// GeospatialPage and the map itself never change.
import "./AprsStationsLayer";
import "./SatelliteTrackLayer";
