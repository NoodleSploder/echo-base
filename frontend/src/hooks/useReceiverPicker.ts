import { useEffect, useState } from "react";
import { listReceivers } from "../api/receivers";
import type { ReceiverDescriptor } from "../types";

// Polls the receiver list and lets single-receiver dashboard widgets
// (Spectrum Monitor) offer a picker instead of hardcoding "whichever
// one shows up first" -- defaults to the first receiver, but keeps
// whatever the user explicitly picked as long as it's still present.
export function useReceiverPicker(): {
  receivers: ReceiverDescriptor[];
  selectedId: string | null;
  setSelectedId: (id: string) => void;
} {
  const [receivers, setReceivers] = useState<ReceiverDescriptor[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const found = await listReceivers();
        if (cancelled) return;
        setReceivers(found);
        setSelectedId((current) => {
          if (current && found.some((r) => r.id === current)) return current;
          return found[0]?.id ?? null;
        });
      } catch {
        if (!cancelled) setReceivers([]);
      }
    }
    void load();
    const interval = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return { receivers, selectedId, setSelectedId };
}
