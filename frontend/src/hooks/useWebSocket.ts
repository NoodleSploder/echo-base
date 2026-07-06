import { useEffect, useRef, useState } from "react";
import type { EchoBaseEvent } from "../types";

export function useEventStream(enabled: boolean) {
  const [events, setEvents] = useState<EchoBaseEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      if (cancelled) return;
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${protocol}://${window.location.host}/ws/events`);
      socketRef.current = socket;

      socket.onopen = () => setConnected(true);
      socket.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          retryTimer = setTimeout(connect, 3000);
        }
      };
      socket.onerror = () => socket.close();
      socket.onmessage = (message) => {
        try {
          const parsed = JSON.parse(message.data as string) as EchoBaseEvent;
          setEvents((prev) => [parsed, ...prev].slice(0, 50));
        } catch {
          // Ignore malformed frames.
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      socketRef.current?.close();
    };
  }, [enabled]);

  return { events, connected };
}
