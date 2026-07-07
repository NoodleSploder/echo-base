import { useEffect, useState } from "react";
import { listAisVessels, type AisVessel } from "../../api/ais";
import { Card } from "../common/Card";

const POLL_INTERVAL_MS = 10000;

// Last-known-contact-per-MMSI (see ais_vessels.py) -- real data once a
// receiver has AIS decoding enabled, tuned to a marine AIS channel
// (161.975MHz/162.025MHz). `receiverId`, if given, filters to just
// that receiver (used as a decoder panel's live view on the Digital
// Modes page); omitted, it shows vessels from every receiver (used on
// the Receivers page as a cross-receiver summary) -- same dual-use
// shape as AdsbAircraftPanel.
export function AisVesselsPanel({ receiverId }: { receiverId?: string } = {}) {
  const [vessels, setVessels] = useState<AisVessel[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await listAisVessels(receiverId);
        if (!cancelled) setVessels(data);
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

  if (vessels.length === 0) {
    return receiverId ? <p className="text-xs text-slate-500">No vessels decoded yet.</p> : null;
  }

  const table = (
    <table className="w-full text-left text-xs">
      <thead className="text-slate-500">
        <tr>
          <th className="pb-1 font-medium">MMSI</th>
          <th className="pb-1 font-medium">Message Type</th>
          <th className="pb-1 font-medium">Position</th>
          <th className="pb-1 font-medium">Messages</th>
          <th className="pb-1 font-medium">First seen</th>
          <th className="pb-1 font-medium">Last seen</th>
        </tr>
      </thead>
      <tbody>
        {vessels.map((v) => (
          <tr key={`${v.receiver_id}-${v.mmsi}`} className="border-t border-base-800">
            <td className="py-1 font-medium text-accent-400">{v.mmsi}</td>
            <td className="py-1 text-slate-400">{v.last_message_type}</td>
            <td className="py-1 text-slate-400">
              {v.latitude !== null && v.longitude !== null
                ? `${v.latitude.toFixed(4)}, ${v.longitude.toFixed(4)}`
                : "-"}
            </td>
            <td className="py-1 text-slate-400">{v.message_count}</td>
            <td className="py-1 text-slate-400">{new Date(v.first_seen_at).toLocaleTimeString()}</td>
            <td className="py-1 text-slate-400">{new Date(v.last_seen_at).toLocaleTimeString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return receiverId ? table : <Card title="AIS Vessels">{table}</Card>;
}
