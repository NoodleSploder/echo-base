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

// Codes the backend closes with intentionally (see spectrum.py): not
// worth retrying since neither condition resolves on its own.
const SPECTRUM_NO_RETRY_CODES = new Set([4401, 4404, 4405]);

export function useSpectrumStream(receiverId: string | null) {
  const [frame, setFrame] = useState<Float32Array | null>(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    setFrame(null);
    setConnected(false);
    if (!receiverId) return;
    const id = receiverId;

    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      if (cancelled) return;
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(
        `${protocol}://${window.location.host}/ws/spectrum/${encodeURIComponent(id)}`,
      );
      socket.binaryType = "arraybuffer";
      socketRef.current = socket;

      socket.onopen = () => setConnected(true);
      socket.onclose = (event) => {
        setConnected(false);
        if (!cancelled && !SPECTRUM_NO_RETRY_CODES.has(event.code)) {
          retryTimer = setTimeout(connect, 3000);
        }
      };
      socket.onerror = () => socket.close();
      socket.onmessage = (message) => {
        if (message.data instanceof ArrayBuffer) {
          setFrame(new Float32Array(message.data));
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      socketRef.current?.close();
    };
  }, [receiverId]);

  return { frame, connected };
}
