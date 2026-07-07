import { useEffect, useState } from "react";
import { listAdsbAircraft, type AdsbAircraft } from "../../api/adsb";
import { Card } from "../common/Card";

const POLL_INTERVAL_MS = 10000;

// Last-known-contact-per-ICAO-address (see adsb_aircraft.py) -- real
// data once a receiver has ADS-B decoding enabled (see the Digital
// Modes page's ADS-B panel, or any decoder pointed at a genuinely
// wideband capture: >=2MS/s, tuned to 1090MHz). Renders nothing if no
// aircraft have been seen recently, rather than an empty table shell
// -- most of the time this will be empty in an environment without a
// 1090MHz-optimized antenna. `receiverId`, if given, filters to just
// that receiver (used when this is a decoder panel's live view);
// omitted, it shows aircraft from every receiver (used on the
// Receivers page as a cross-receiver summary).
export function AdsbAircraftPanel({ receiverId }: { receiverId?: string } = {}) {
  const [aircraft, setAircraft] = useState<AdsbAircraft[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await listAdsbAircraft(receiverId);
        if (!cancelled) setAircraft(data);
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

  // Used two ways: as a global cross-receiver summary on the Receivers
  // page (no receiverId -- keeps its own Card chrome, hidden entirely
  // when empty), and as a decoder panel's live view on the Digital
  // Modes page (a receiverId is always given there -- the wrapping
  // DecoderPanel already supplies chrome, so this renders a plain
  // "nothing yet" message instead of disappearing, since a panel
  // should never look broken/blank with no explanation).
  if (aircraft.length === 0) {
    return receiverId ? <p className="text-xs text-slate-500">No aircraft decoded yet.</p> : null;
  }

  const table = (
    <table className="w-full text-left text-xs">
      <thead className="text-slate-500">
        <tr>
          <th className="pb-1 font-medium">ICAO</th>
          <th className="pb-1 font-medium">Type Code</th>
          <th className="pb-1 font-medium">Messages</th>
          <th className="pb-1 font-medium">First seen</th>
          <th className="pb-1 font-medium">Last seen</th>
        </tr>
      </thead>
      <tbody>
        {aircraft.map((a) => (
          <tr key={`${a.receiver_id}-${a.icao}`} className="border-t border-base-800">
            <td className="py-1 font-medium text-accent-400">{a.icao}</td>
            <td className="py-1 text-slate-400">{a.last_type_code}</td>
            <td className="py-1 text-slate-400">{a.message_count}</td>
            <td className="py-1 text-slate-400">{new Date(a.first_seen_at).toLocaleTimeString()}</td>
            <td className="py-1 text-slate-400">{new Date(a.last_seen_at).toLocaleTimeString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return receiverId ? table : <Card title="ADS-B Aircraft">{table}</Card>;
}
