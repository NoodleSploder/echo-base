import { useEventStreamContext } from "../../context/EventStreamContext";
import { Panel } from "../common/Panel";

// Real data: the internal event bus, streamed over /ws/events. Sparse
// until more subsystems (Phase 3+) start publishing domain events.
export function ActivityFeedWidget() {
  const { events } = useEventStreamContext();

  return (
    <Panel title="Activity Feed" bodyClassName="space-y-1 p-2">
      {events.length === 0 && (
        <p className="p-2 text-xs text-slate-500">
          No events yet. Start a receiver or wait for plugin activity to see live events here.
        </p>
      )}
      {events.map((event) => (
        <div key={event.id} className="flex items-center justify-between rounded-md bg-base-800/50 px-2 py-1.5 text-xs">
          <span className="font-medium text-slate-200">{event.type}</span>
          <span className="text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
        </div>
      ))}
    </Panel>
  );
}
