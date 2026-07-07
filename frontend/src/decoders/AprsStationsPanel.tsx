import { useEffect, useState } from "react";
import { listAprsStations, type AprsStation } from "../api/aprs";
import type { DecoderPanelProps } from "./types";

const POLL_INTERVAL_MS = 10000;

// Last-known position per callsign (see aprs_stations.py) -- real data
// once this decoder is pointed at a receiver tuned to a real APRS
// frequency (144.390MHz in North America).
export function AprsStationsPanel({ receiverId }: DecoderPanelProps) {
  const [stations, setStations] = useState<AprsStation[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await listAprsStations(receiverId);
        if (!cancelled) setStations(data);
      } catch {
        // Transient poll failure; keep showing the last good list.
      }
    }
    void poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [receiverId]);

  if (stations.length === 0) {
    return <p className="text-xs text-slate-500">No stations decoded yet.</p>;
  }

  return (
    <table className="w-full text-left text-xs">
      <thead className="text-slate-500">
        <tr>
          <th className="pb-1 font-medium">Callsign</th>
          <th className="pb-1 font-medium">Position</th>
          <th className="pb-1 font-medium">Info</th>
          <th className="pb-1 font-medium">Last heard</th>
        </tr>
      </thead>
      <tbody>
        {stations.map((s) => (
          <tr key={`${s.receiver_id}-${s.callsign}`} className="border-t border-base-800">
            <td className="py-1 font-medium text-accent-400">{s.callsign}</td>
            <td className="py-1 text-slate-400">
              {s.latitude.toFixed(4)}, {s.longitude.toFixed(4)}
            </td>
            <td className="py-1 text-slate-400">{s.last_info}</td>
            <td className="py-1 text-slate-400">{new Date(s.last_heard_at).toLocaleTimeString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
