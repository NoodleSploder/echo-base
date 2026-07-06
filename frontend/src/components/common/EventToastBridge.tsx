import { useEffect, useRef } from "react";
import { useEventStreamContext } from "../../context/EventStreamContext";
import { useToast } from "../../context/ToastContext";

// Turns a handful of high-signal event types into toasts. Deliberately
// not every event type: AprsPacket/SignalDetected fire often enough
// during normal operation that toasting each one would just be noise
// on top of the Activity Feed/System Log widgets, which already show
// everything. SameAlert is the opposite -- rare and worth
// interrupting the user for (it's a real NOAA/EAS emergency alert) --
// and ReceiverStarted/Stopped are useful confirmation for an action
// the user just took.
export function EventToastBridge() {
  const { events } = useEventStreamContext();
  const { pushToast } = useToast();
  const seenIds = useRef(new Set<string>());

  useEffect(() => {
    const stillPresent = new Set<string>();
    for (const event of events) {
      stillPresent.add(event.id);
      if (seenIds.current.has(event.id)) continue;

      if (event.type === "SameAlert") {
        const eventName = String(event.data.event_name ?? event.data.event_code ?? "Alert");
        const locations = Array.isArray(event.data.location_names)
          ? (event.data.location_names as string[]).join(", ")
          : undefined;
        pushToast({
          variant: "danger",
          title: `NOAA Alert: ${eventName}`,
          message: locations || String(event.source),
        });
      } else if (event.type === "ReceiverStarted" || event.type === "ReceiverStopped") {
        // Emitted with source="plugin:<id>" -- the receiver_id itself
        // (what the user actually recognizes) lives in `data`.
        const receiverId = String(event.data.receiver_id ?? event.source);
        const verb = event.type === "ReceiverStarted" ? "started" : "stopped";
        pushToast({ variant: "info", title: `${receiverId} ${verb}` });
      } else if (event.type === "ReceiverConnected") {
        pushToast({ variant: "info", title: `${event.source} connected` });
      } else if (event.type === "ReceiverDisconnected") {
        pushToast({ variant: "warning", title: `${event.source} disconnected` });
      }
    }
    // Rebuilt from the (size-capped, at most 50) events list each run,
    // rather than only ever growing -- keeps this bounded instead of
    // accumulating every event id seen for the lifetime of the tab.
    seenIds.current = stillPresent;
  }, [events, pushToast]);

  return null;
}
