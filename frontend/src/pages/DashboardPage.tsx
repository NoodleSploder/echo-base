import { useEventStreamContext } from "../context/EventStreamContext";
import { HealthWidget } from "../components/system/HealthWidget";

export function DashboardPage() {
  const { events } = useEventStreamContext();

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="lg:col-span-1">
        <HealthWidget />
      </div>
      <div className="rounded-lg border border-base-700 bg-base-900/60 p-4 lg:col-span-2">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-300">Live activity</h2>
        {events.length === 0 && <p className="text-sm text-slate-500">No events yet.</p>}
        <ul className="space-y-2">
          {events.map((event) => (
            <li
              key={event.id}
              className="flex items-center justify-between rounded-md bg-base-800/60 px-3 py-2 text-sm"
            >
              <span className="text-slate-200">{event.type}</span>
              <span className="text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
