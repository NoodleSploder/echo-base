import { useCallback, useEffect, useState } from "react";
import { discoverReceivers, listReceivers } from "../../api/receivers";
import type { ReceiverDescriptor, ReceiverStatus } from "../../types";
import { AdsbAircraftPanel } from "./AdsbAircraftPanel";
import { AisVesselsPanel } from "./AisVesselsPanel";
import { ReceiverCard } from "./ReceiverCard";
import { ReceiverInventoryPanel } from "./ReceiverInventoryPanel";
import { ReceiverProfilesPanel } from "./ReceiverProfilesPanel";

export function ReceiverList() {
  const [receivers, setReceivers] = useState<ReceiverDescriptor[]>([]);
  const [statuses, setStatuses] = useState<Record<string, ReceiverStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setReceivers(await listReceivers());
      setError(null);
    } catch {
      setError("Unable to load receivers.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleDiscover() {
    setLoading(true);
    try {
      setReceivers(await discoverReceivers());
      setError(null);
    } catch {
      setError("Discovery failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-100">Receivers</h1>
        <button
          onClick={() => void handleDiscover()}
          className="rounded-md border border-base-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-base-800"
        >
          Re-scan hardware
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {!error && !loading && receivers.length === 0 && (
        <p className="text-sm text-slate-500">
          No receivers detected. Connect an SDR (e.g. an RTL-SDR dongle) and click &quot;Re-scan hardware&quot;.
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {receivers.map((receiver) => (
          <ReceiverCard
            key={receiver.id}
            receiver={receiver}
            status={statuses[receiver.id]}
            onChange={(status) => setStatuses((prev) => ({ ...prev, [receiver.id]: status }))}
          />
        ))}
      </div>

      <ReceiverProfilesPanel
        receivers={receivers}
        onApplied={(receiverId, status) => setStatuses((prev) => ({ ...prev, [receiverId]: status }))}
      />

      <ReceiverInventoryPanel />
      <AdsbAircraftPanel />
      <AisVesselsPanel />
    </div>
  );
}
