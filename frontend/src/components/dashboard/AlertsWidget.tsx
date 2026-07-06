import { useMemo } from "react";
import { useEventStreamContext } from "../../context/EventStreamContext";
import { Panel } from "../common/Panel";
import { SAMPLE_ALERTS } from "../../lib/sampleData";

const SEVERITY_CLASSES: Record<string, string> = {
  info: "bg-sky-500/15 text-sky-400",
  warning: "bg-amber-500/15 text-amber-400",
  critical: "bg-red-500/15 text-red-400",
};

// A handful of common NOAA SAME event codes; anything else defaults to
// "warning" since the vast majority of codes are actual hazard alerts,
// not tests -- see https://www.weather.gov/nwr/eventcodes for the full list.
const TEST_EVENT_CODES = new Set(["RWT", "RMT"]);
const CRITICAL_EVENT_CODES = new Set(["TOR", "EWW", "FFW", "EAN"]);

function severityForEventCode(eventCode: string): "info" | "warning" | "critical" {
  if (TEST_EVENT_CODES.has(eventCode)) return "info";
  if (CRITICAL_EVENT_CODES.has(eventCode)) return "critical";
  return "warning";
}

// Real data once a receiver has "Decode SAME" enabled (see
// ReceiverCard) -- decoded NOAA Weather Radio alerts arrive as
// "SameAlert" events over the same event-bus WebSocket the Activity
// Feed/System Log widgets already use.
export function AlertsWidget() {
  const { events } = useEventStreamContext();

  const sameAlerts = useMemo(() => events.filter((event) => event.type === "SameAlert"), [events]);
  const hasRealAlerts = sameAlerts.length > 0;

  return (
    <Panel
      title={`Alerts ${hasRealAlerts ? sameAlerts.length : SAMPLE_ALERTS.length} Active`}
      sample={!hasRealAlerts}
      bodyClassName="space-y-1.5 p-2"
    >
      {hasRealAlerts
        ? sameAlerts.map((event) => {
            const eventCode = String(event.data.event_code ?? "");
            const eventName = String(event.data.event_name ?? eventCode);
            const severity = severityForEventCode(eventCode);
            const locationNames = Array.isArray(event.data.location_names)
              ? event.data.location_names
              : [];
            return (
              <div key={event.id} className="flex items-start gap-2 rounded-md bg-base-800/50 px-2 py-1.5 text-xs">
                <span
                  className={`mt-0.5 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${SEVERITY_CLASSES[severity]}`}
                >
                  {severity}
                </span>
                <div className="flex-1">
                  <div className="text-slate-200">{eventName}</div>
                  <div className="text-slate-500">{locationNames.join("; ")}</div>
                  <div className="text-slate-500">
                    {String(event.data.station ?? event.source)} &middot;{" "}
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            );
          })
        : SAMPLE_ALERTS.map((alert) => (
            <div key={alert.id} className="flex items-start gap-2 rounded-md bg-base-800/50 px-2 py-1.5 text-xs">
              <span className={`mt-0.5 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${SEVERITY_CLASSES[alert.severity]}`}>
                {alert.severity}
              </span>
              <div className="flex-1">
                <div className="text-slate-200">{alert.message}</div>
                <div className="text-slate-500">
                  {alert.source} &middot; {alert.time}
                </div>
              </div>
            </div>
          ))}
      <button type="button" disabled className="w-full cursor-not-allowed rounded-md border border-base-600 py-1.5 text-xs text-slate-500">
        View All Alerts
      </button>
    </Panel>
  );
}
