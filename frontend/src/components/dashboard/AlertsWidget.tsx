import { Panel } from "../common/Panel";
import { SAMPLE_ALERTS } from "../../lib/sampleData";

const SEVERITY_CLASSES: Record<string, string> = {
  info: "bg-sky-500/15 text-sky-400",
  warning: "bg-amber-500/15 text-amber-400",
  critical: "bg-red-500/15 text-red-400",
};

export function AlertsWidget() {
  return (
    <Panel title={`Alerts ${SAMPLE_ALERTS.length} Active`} sample bodyClassName="space-y-1.5 p-2">
      {SAMPLE_ALERTS.map((alert) => (
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
