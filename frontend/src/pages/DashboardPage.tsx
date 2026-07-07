import { useCallback, useEffect, useRef, useState, type ComponentType } from "react";
import { Responsive, WidthProvider, type Layout } from "react-grid-layout";
import { getDashboardLayout, saveDashboardLayout } from "../api/dashboard";
import { ActivityFeedWidget } from "../components/dashboard/ActivityFeedWidget";
import { AlertsWidget } from "../components/dashboard/AlertsWidget";
import { Ft8MessagesWidget } from "../components/dashboard/Ft8MessagesWidget";
import { MessagingCenterWidget } from "../components/dashboard/MessagingCenterWidget";
import { ReceiverTileGridWidget } from "../components/dashboard/ReceiverTileGridWidget";
import { ReceiversPanelWidget } from "../components/dashboard/ReceiversPanelWidget";
import { RecordingsWidget } from "../components/dashboard/RecordingsWidget";
import { SpectrumMonitorWidget } from "../components/dashboard/SpectrumMonitorWidget";
import { SpectrumOverviewWidget } from "../components/dashboard/SpectrumOverviewWidget";
import { SystemLogWidget } from "../components/dashboard/SystemLogWidget";
import { SystemStatusWidget } from "../components/dashboard/SystemStatusWidget";

const ResponsiveGridLayout = WidthProvider(Responsive);
const ROW_HEIGHT = 28;
const SAVE_DEBOUNCE_MS = 800;

type LayoutsMap = Record<string, Layout[]>;

const WIDGET_COMPONENTS: Record<string, ComponentType> = {
  receivers: ReceiversPanelWidget,
  spectrumOverview: SpectrumOverviewWidget,
  activityFeed: ActivityFeedWidget,
  systemStatus: SystemStatusWidget,
  receiverTiles: ReceiverTileGridWidget,
  alerts: AlertsWidget,
  messaging: MessagingCenterWidget,
  recordings: RecordingsWidget,
  spectrumMonitor: SpectrumMonitorWidget,
  systemLog: SystemLogWidget,
  ft8Messages: Ft8MessagesWidget,
};

// Per-protocol decoder *configuration* (which receiver a decoder is
// pointed at, start/stop) lives on the dedicated Digital Modes page
// now -- see decoders/DecoderPanel.tsx. ft8Messages is different: a
// read-only live summary (real data, across every receiver already
// decoding FT8), the same "just show what's already been decoded"
// shape as ActivityFeedWidget, not a configuration surface -- so it
// stays on the Dashboard alongside the other live-status widgets.
const DEFAULT_LG_LAYOUT: Layout[] = [
  { i: "receivers", x: 0, y: 0, w: 3, h: 10, minW: 2, minH: 6 },
  { i: "spectrumOverview", x: 3, y: 0, w: 6, h: 10, minW: 4, minH: 6 },
  { i: "activityFeed", x: 9, y: 0, w: 3, h: 10, minW: 2, minH: 6 },
  { i: "systemStatus", x: 0, y: 10, w: 3, h: 8, minW: 2, minH: 6 },
  { i: "receiverTiles", x: 3, y: 10, w: 9, h: 8, minW: 4, minH: 6 },
  { i: "alerts", x: 0, y: 18, w: 3, h: 8, minW: 2, minH: 5 },
  { i: "messaging", x: 3, y: 18, w: 4, h: 8, minW: 2, minH: 6 },
  { i: "recordings", x: 7, y: 18, w: 3, h: 8, minW: 3, minH: 5 },
  { i: "spectrumMonitor", x: 0, y: 26, w: 5, h: 8, minW: 3, minH: 5 },
  { i: "systemLog", x: 5, y: 26, w: 5, h: 8, minW: 3, minH: 5 },
  { i: "ft8Messages", x: 0, y: 34, w: 6, h: 8, minW: 3, minH: 5 },
];

function stackedLayout(cols: number): Layout[] {
  let y = 0;
  return DEFAULT_LG_LAYOUT.map((item) => {
    const stacked: Layout = { ...item, x: 0, y, w: cols };
    y += item.h;
    return stacked;
  });
}

const DEFAULT_LAYOUTS: LayoutsMap = {
  lg: DEFAULT_LG_LAYOUT,
  md: stackedLayout(8),
  sm: stackedLayout(4),
};

export function DashboardPage() {
  const [layouts, setLayouts] = useState<LayoutsMap>(DEFAULT_LAYOUTS);
  const [ready, setReady] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    let cancelled = false;
    getDashboardLayout()
      .then((data) => {
        if (!cancelled && data.layout) {
          setLayouts(data.layout as LayoutsMap);
        }
      })
      .catch(() => {
        // No saved layout yet (or not reachable) -- defaults are fine.
      })
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLayoutChange = useCallback((_current: Layout[], allLayouts: LayoutsMap) => {
    setLayouts(allLayouts);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      void saveDashboardLayout(allLayouts);
    }, SAVE_DEBOUNCE_MS);
  }, []);

  function resetLayout() {
    setLayouts(DEFAULT_LAYOUTS);
    void saveDashboardLayout(DEFAULT_LAYOUTS);
  }

  if (!ready) {
    return <div className="p-6 text-sm text-slate-500">Loading dashboard...</div>;
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs text-slate-500">Drag panels by their header to rearrange; drag a corner to resize.</p>
        <button
          type="button"
          onClick={resetLayout}
          className="rounded-md border border-base-600 px-3 py-1.5 text-xs text-slate-300 hover:bg-base-800"
        >
          Reset Layout
        </button>
      </div>
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768 }}
        cols={{ lg: 12, md: 8, sm: 4 }}
        rowHeight={ROW_HEIGHT}
        margin={[12, 12]}
        draggableHandle=".drag-handle"
        onLayoutChange={handleLayoutChange}
      >
        {Object.keys(WIDGET_COMPONENTS).map((key) => {
          const Widget = WIDGET_COMPONENTS[key];
          return (
            <div key={key}>
              <Widget />
            </div>
          );
        })}
      </ResponsiveGridLayout>
    </div>
  );
}
