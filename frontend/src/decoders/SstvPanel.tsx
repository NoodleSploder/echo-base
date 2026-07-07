import { useEffect, useState } from "react";
import { getSstvSnapshot, sstvImagePath } from "../api/receivers";
import type { DecoderPanelProps } from "./types";

// Only ever mounted while the SSTV decoder is enabled (see
// ReceiverDecoders), so this can poll unconditionally for as long as
// it's alive rather than gating on an "enabled" prop.
export function SstvPanel({ receiverId }: DecoderPanelProps) {
  const [snapshot, setSnapshot] = useState<{ linesDecoded: number; totalLines: number } | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const result = await getSstvSnapshot(receiverId);
        if (!cancelled) {
          setSnapshot({ linesDecoded: result.lines_decoded, totalLines: result.total_lines });
        }
      } catch {
        // Transient poll failure; keep showing the last good reading.
      }
    }
    void poll();
    // Fast enough to feel like watching the image draw in live, slow
    // enough not to hammer the endpoint -- a full 256-line Martin M1
    // image takes ~2 minutes to transmit, so a new line every second
    // or so is still a meaningfully "live" refresh rate.
    const interval = setInterval(poll, 1000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [receiverId]);

  return (
    <div className="border-t border-base-700 pt-3">
      <div className="mb-1 flex items-center justify-between text-[11px] text-slate-400">
        <span>SSTV Image (Martin M1)</span>
        {snapshot && (
          <span>
            {snapshot.linesDecoded} / {snapshot.totalLines} lines
            {snapshot.linesDecoded >= snapshot.totalLines && (
              <span className="ml-1 text-emerald-400">complete</span>
            )}
          </span>
        )}
      </div>
      <div className="overflow-hidden rounded-md border border-base-700 bg-black">
        <img
          src={`${sstvImagePath(receiverId)}?t=${snapshot?.linesDecoded ?? 0}`}
          alt="Live-decoding SSTV picture"
          className="w-full"
          style={{ imageRendering: "pixelated" }}
        />
      </div>
    </div>
  );
}
