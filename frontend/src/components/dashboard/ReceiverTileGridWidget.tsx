import { useEffect, useState } from "react";
import { getReceiver, listReceivers } from "../../api/receivers";
import { useSpectrumStream } from "../../hooks/useWebSocket";
import type { ReceiverDescriptor, ReceiverState, ReceiverStatus } from "../../types";
import { Panel } from "../common/Panel";
import { SpectrumCanvas } from "../common/SpectrumCanvas";

const STATE_BADGE: Record<ReceiverState, string> = {
  streaming: "bg-emerald-500/15 text-emerald-400",
  idle: "bg-slate-500/15 text-slate-400",
  error: "bg-red-500/15 text-red-400",
  disconnected: "bg-slate-600/15 text-slate-500",
};

function formatFrequency(hz: number | null): string {
  return hz === null ? "--" : `${(hz / 1e6).toFixed(3)} MHz`;
}

function ReceiverTile({ receiver, status }: { receiver: ReceiverDescriptor; status: ReceiverStatus | undefined }) {
  const state = status?.state ?? "disconnected";
  // Subscribing here opens a live capture for this receiver (see
  // StreamService) for as long as this tile is mounted -- consistent
  // with "an unwatched dashboard doesn't tie up hardware," a mounted
  // Receiver Tiles widget *is* watching every receiver it shows.
  const { frame, connected } = useSpectrumStream(
    receiver.capabilities.iq_streaming === true ? receiver.id : null,
  );

  return (
    <div className="rounded-md border border-base-700 bg-base-800/40 p-2">
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 font-semibold text-slate-200">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
          {receiver.name}
        </span>
        <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${STATE_BADGE[state]}`}>
          {state}
        </span>
      </div>
      <div className="mb-1 font-mono text-lg text-slate-100">{formatFrequency(status?.frequency_hz ?? null)}</div>
      <div className="relative">
        <SpectrumCanvas height={56} liveFrame={frame} />
        {!connected && (
          <span className="absolute right-1 top-1 rounded bg-black/50 px-1 text-[9px] uppercase text-amber-400">
            sample
          </span>
        )}
      </div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-slate-400">
        <span>
          Driver <span className="text-slate-200">{receiver.driver}</span>
        </span>
        {status?.gain !== null && status?.gain !== undefined && (
          <span>
            Gain <span className="text-slate-200">{status.gain}</span>
          </span>
        )}
      </div>
    </div>
  );
}

// Real data: GET /api/receivers + GET /api/receivers/{id} per device,
// on the same poll cadence as ReceiversPanelWidget. Each tile's
// waterfall is real live spectrum data (see StreamService) for
// receivers that support IQ streaming, falling back to the decorative
// sample animation otherwise.
export function ReceiverTileGridWidget() {
  const [receivers, setReceivers] = useState<ReceiverDescriptor[]>([]);
  const [statuses, setStatuses] = useState<Record<string, ReceiverStatus>>({});
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const list = await listReceivers();
        if (cancelled) return;
        setReceivers(list);
        const entries = await Promise.all(
          list.map(async (receiver) => {
            try {
              return [receiver.id, await getReceiver(receiver.id)] as const;
            } catch {
              return null;
            }
          }),
        );
        if (!cancelled) {
          setStatuses(Object.fromEntries(entries.filter((entry): entry is [string, ReceiverStatus] => entry !== null)));
        }
      } catch {
        // Leave prior state in place; System Status widget already
        // surfaces backend connectivity problems prominently.
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
    <Panel title="Receiver Tiles" bodyClassName="p-3">
      {loaded && receivers.length === 0 && (
        <p className="p-2 text-xs text-slate-500">
          No receivers detected. Discover hardware from the Receivers page.
        </p>
      )}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {receivers.map((receiver) => (
          <ReceiverTile key={receiver.id} receiver={receiver} status={statuses[receiver.id]} />
        ))}
      </div>
    </Panel>
  );
}
