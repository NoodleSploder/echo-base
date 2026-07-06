import { useEffect, useState } from "react";
import { listReceivers } from "../api/receivers";

// Picks the first discovered receiver so single-receiver dashboard
// widgets (Spectrum Monitor/Overview) have something to stream from
// without the user manually selecting one -- see ROADMAP.md's
// multi-receiver UI, which will replace this with an explicit picker.
export function useFirstReceiver(): string | null {
  const [receiverId, setReceiverId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const receivers = await listReceivers();
        if (!cancelled) setReceiverId(receivers[0]?.id ?? null);
      } catch {
        if (!cancelled) setReceiverId(null);
      }
    }
    void load();
    const interval = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return receiverId;
}
