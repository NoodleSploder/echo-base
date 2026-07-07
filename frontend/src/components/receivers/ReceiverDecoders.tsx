import { useEffect, useState } from "react";
import type { CaptureHealth } from "../../api/receivers";
import { getRegisteredDecoders, isInBand } from "../../decoders/DecoderRegistry";
import "../../decoders"; // side-effect import: every decoder module registers itself

// Renders one toggle per registered protocol decoder (APRS, SAME,
// ADS-B, AIS, SSTV, FT8, ...), de-emphasized (not hidden -- so an
// already-running decoder is never lost from view if the receiver
// gets retuned out of its band) when the receiver's current tuning
// falls outside that decoder's typical frequency range. Adding a new
// decoder never touches this component -- see decoders/DecoderRegistry.ts.
export function ReceiverDecoders({
  receiverId,
  frequencyHz,
  captureHealth,
}: {
  receiverId: string;
  frequencyHz: number | null;
  captureHealth: CaptureHealth | null;
}) {
  const decoders = getRegisteredDecoders();
  const [enabled, setEnabled] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState<Record<string, boolean>>({});

  // Always syncs from the shared capture-health poll (passed down by
  // ReceiverCard) rather than polling its own copy, so a decoder
  // enabled from elsewhere -- e.g. a suggested receiver profile that
  // enables it server-side directly -- is reflected here too.
  useEffect(() => {
    if (!captureHealth) return;
    setEnabled((prev) => {
      let changed = false;
      const next = { ...prev };
      for (const decoder of decoders) {
        const value = captureHealth[decoder.healthKey];
        if (typeof value === "boolean" && next[decoder.id] !== value) {
          next[decoder.id] = value;
          changed = true;
        }
      }
      return changed ? next : prev;
    });
    // `decoders` is a stable module-level registry snapshot -- it
    // never changes identity across renders, so it's not a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [captureHealth]);

  async function handleToggle(decoderId: string) {
    const decoder = decoders.find((d) => d.id === decoderId);
    if (!decoder) return;
    setBusy((prev) => ({ ...prev, [decoderId]: true }));
    try {
      if (enabled[decoderId]) {
        await decoder.stop(receiverId);
      } else {
        await decoder.start(receiverId);
      }
      setEnabled((prev) => ({ ...prev, [decoderId]: !prev[decoderId] }));
    } finally {
      setBusy((prev) => ({ ...prev, [decoderId]: false }));
    }
  }

  return (
    <div className="border-t border-base-700 pt-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Decoders</h2>
      <div className="flex flex-wrap gap-2">
        {decoders.map((decoder) => {
          const inBand = isInBand(decoder, frequencyHz);
          const isEnabled = enabled[decoder.id] ?? false;
          return (
            <button
              key={decoder.id}
              type="button"
              onClick={() => void handleToggle(decoder.id)}
              disabled={busy[decoder.id]}
              title={`${decoder.description}${
                decoder.feedsMapLayer ? " Feeds the Geospatial map when enabled." : ""
              }${inBand ? "" : " (outside this decoder's typical frequency range for the current tuning)"}`}
              className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-opacity disabled:opacity-50 ${
                isEnabled
                  ? "bg-accent-500/20 text-accent-400 hover:bg-accent-500/30"
                  : "border border-base-600 text-slate-300 hover:bg-base-800"
              } ${inBand ? "" : "opacity-50"}`}
            >
              {decoder.name}
              {isEnabled ? " On" : ""}
            </button>
          );
        })}
      </div>
      {decoders.map((decoder) => {
        const Panel = decoder.Panel;
        if (!Panel || !enabled[decoder.id]) return null;
        return <Panel key={decoder.id} receiverId={receiverId} />;
      })}
    </div>
  );
}
