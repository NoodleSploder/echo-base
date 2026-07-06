import { useEffect, useState } from "react";
import { getReceiverInventory, type ReceiverInventoryRecord } from "../../api/receivers";
import { Card } from "../common/Card";

const POLL_INTERVAL_MS = 15000;

// Every receiver this deployment has ever seen, including ones no
// longer attached -- distinct from the cards above, which only ever
// show what's currently plugged in (GET /api/receivers re-runs live
// discovery on every call). Backed by HotplugMonitor's periodic
// discovery polls (see receiver_inventory.py), not this panel's own
// polling, which is just for display.
export function ReceiverInventoryPanel() {
  const [records, setRecords] = useState<ReceiverInventoryRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await getReceiverInventory();
        if (!cancelled) {
          setRecords(data);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("Unable to load receiver inventory.");
      }
    }
    void poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (records.length === 0 && !error) return null;

  return (
    <Card title="Receiver Inventory">
      {error && <p className="text-sm text-red-400">{error}</p>}
      <table className="w-full text-left text-xs">
        <thead className="text-slate-500">
          <tr>
            <th className="pb-1 font-medium">Receiver</th>
            <th className="pb-1 font-medium">Driver</th>
            <th className="pb-1 font-medium">Serial</th>
            <th className="pb-1 font-medium">First seen</th>
            <th className="pb-1 font-medium">Last seen</th>
            <th className="pb-1 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.receiver_id} className="border-t border-base-800">
              <td className="py-1 text-slate-200">{record.name}</td>
              <td className="py-1 text-slate-400">{record.driver}</td>
              <td className="py-1 text-slate-400">{record.serial ?? "-"}</td>
              <td className="py-1 text-slate-400">{new Date(record.first_seen_at).toLocaleString()}</td>
              <td className="py-1 text-slate-400">{new Date(record.last_seen_at).toLocaleString()}</td>
              <td className="py-1">
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    record.attached
                      ? "bg-emerald-500/15 text-emerald-400"
                      : "bg-slate-700/40 text-slate-500"
                  }`}
                >
                  {record.attached ? "Attached" : "Not attached"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
