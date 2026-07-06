import { useEventStreamContext } from "../../context/EventStreamContext";
import { Panel } from "../common/Panel";

// Real data: the same internal event bus as the Activity Feed widget,
// formatted as leveled log lines instead of a plain feed.
export function SystemLogWidget() {
  const { events } = useEventStreamContext();

  return (
    <Panel title="System Log" bodyClassName="p-2 font-mono text-xs">
      {events.length === 0 && <p className="p-2 text-slate-500">No log entries yet.</p>}
      <ul className="space-y-0.5">
        {events.map((event) => (
          <li key={event.id} className="truncate">
            <span className="text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</span>{" "}
            <span className="text-sky-400">[INFO]</span>{" "}
            <span className="text-slate-300">
              {event.source}: {event.type}
            </span>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
