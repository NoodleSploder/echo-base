import { createContext, useContext, type ReactNode } from "react";
import { useEventStream } from "../hooks/useWebSocket";
import type { EchoBaseEvent } from "../types";

interface EventStreamValue {
  events: EchoBaseEvent[];
  connected: boolean;
}

const EventStreamContext = createContext<EventStreamValue | undefined>(undefined);

// A single shared WebSocket connection for the whole authenticated app
// shell, so the topbar status indicator and the dashboard activity feed
// don't each open their own socket.
export function EventStreamProvider({ enabled, children }: { enabled: boolean; children: ReactNode }) {
  const value = useEventStream(enabled);
  return <EventStreamContext.Provider value={value}>{children}</EventStreamContext.Provider>;
}

export function useEventStreamContext(): EventStreamValue {
  const ctx = useContext(EventStreamContext);
  if (!ctx) throw new Error("useEventStreamContext must be used within an EventStreamProvider");
  return ctx;
}
