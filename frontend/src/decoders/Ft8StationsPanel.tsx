import { useEffect, useState } from "react";
import { listFt8Stations, type Ft8Station } from "../api/ft8";

const POLL_INTERVAL_MS = 10000;

// Last-known contact per call_de (see ft8_stations.py) -- real data
// once a receiver is decoding FT8, tuned to a real dial frequency
// (USB). A whole ~15s slot has to complete before anything shows up
// here, so this can look empty for a while even with real signal
// present. `receiverId`, if given, filters to just that receiver
// (used as a DecoderPanel's live view on the Digital Modes page);
// omitted, it shows stations from every receiver (used on the
// Dashboard as a live summary widget) -- same dual-use shape as
// AdsbAircraftPanel/AisVesselsPanel.
export function Ft8StationsPanel({ receiverId }: { receiverId?: string } = {}) {
  const [stations, setStations] = useState<Ft8Station[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await listFt8Stations(receiverId);
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
          <th className="pb-1 font-medium">Grid</th>
          <th className="pb-1 font-medium">Message</th>
          <th className="pb-1 font-medium">Freq offset</th>
          <th className="pb-1 font-medium">Messages</th>
          <th className="pb-1 font-medium">Last heard</th>
        </tr>
      </thead>
      <tbody>
        {stations.map((s) => (
          <tr key={`${s.receiver_id}-${s.callsign}`} className="border-t border-base-800">
            <td className="py-1 font-medium text-accent-400">{s.callsign}</td>
            <td className="py-1 text-slate-400">{s.grid ?? "-"}</td>
            <td className="py-1 text-slate-400">{s.last_message}</td>
            <td className="py-1 text-slate-400">{s.frequency_offset_hz.toFixed(0)}Hz</td>
            <td className="py-1 text-slate-400">{s.message_count}</td>
            <td className="py-1 text-slate-400">{new Date(s.last_heard_at).toLocaleTimeString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
