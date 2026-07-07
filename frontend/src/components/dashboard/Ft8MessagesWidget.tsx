import { Ft8StationsPanel } from "../../decoders/Ft8StationsPanel";
import { Panel } from "../common/Panel";

// Real data, across every receiver currently decoding FT8 (see
// ft8_stations.py) -- a live summary, not configurable from here. To
// point a specific receiver at FT8 (or change its settings), use the
// FT8 panel on the Digital Modes page instead; this widget just shows
// whatever's already been decoded anywhere.
export function Ft8MessagesWidget() {
  return (
    <Panel title="FT8 Messages" bodyClassName="p-2">
      <Ft8StationsPanel />
    </Panel>
  );
}
