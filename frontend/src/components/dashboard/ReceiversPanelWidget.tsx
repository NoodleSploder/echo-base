import { useEffect, useState } from "react";
import { listReceivers } from "../../api/receivers";
import type { ReceiverDescriptor } from "../../types";
import { Panel } from "../common/Panel";

// Real data: GET /api/receivers. Empty until hardware is attached and
// discovered -- see ReceiversPage for the full discover/start/stop/tune flow.
export function ReceiversPanelWidget() {
  const [receivers, setReceivers] = useState<ReceiverDescriptor[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await listReceivers();
        if (!cancelled) setReceivers(data);
      } catch {
        // Leave the list empty; System Status widget already surfaces
        // backend connectivity problems prominently.
      } finally {
        if (!cancelled) setLoaded(true);
      }
    }
    void load();
    const interval = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <Panel title={`Receivers ${receivers.length} Online`} bodyClassName="p-2">
      {loaded && receivers.length === 0 && (
        <p className="p-2 text-xs text-slate-500">
          No receivers detected. Discover hardware from the Receivers page.
        </p>
      )}
      <ul className="space-y-1">
        {receivers.map((receiver, index) => (
          <li
            key={receiver.id}
            className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-base-800"
          >
            <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
            <span className="w-6 shrink-0 font-mono text-slate-500">R{index + 1}</span>
            <span className="flex-1 truncate text-slate-200">{receiver.name}</span>
            <span className="shrink-0 font-mono text-slate-400">{receiver.driver}</span>
          </li>
        ))}
      </ul>
      <button
        type="button"
        disabled
        title="Backend wiring for adding receivers lands with Receiver Profiles (see ROADMAP.md)"
        className="mt-2 w-full cursor-not-allowed rounded-md border border-base-600 py-1.5 text-xs text-slate-500"
      >
        + Add Receiver
      </button>
    </Panel>
  );
}
