import { useMemo, useState } from "react";
import { useEventStreamContext } from "../../context/EventStreamContext";
import { Panel } from "../common/Panel";
import { MESSAGING_TABS, SAMPLE_APRS_MESSAGES } from "../../lib/sampleData";

// APRS tab: real data once a receiver has "Decode APRS" enabled (see
// ReceiverCard) -- decoded packets arrive as "AprsPacket" events over
// the same event-bus WebSocket the Activity Feed/System Log widgets
// already use. Other tabs (Winlink, JS8Call, etc.) stay sample data
// pending their own backend subsystems.
export function MessagingCenterWidget() {
  const [activeTab, setActiveTab] = useState("APRS");
  const { events } = useEventStreamContext();

  const aprsPackets = useMemo(
    () => events.filter((event) => event.type === "AprsPacket"),
    [events],
  );
  const hasRealAprsData = activeTab === "APRS" && aprsPackets.length > 0;

  return (
    <Panel title="Messaging Center" sample={!hasRealAprsData} bodyClassName="flex flex-col p-3">
      <div className="mb-2 flex flex-wrap gap-1 border-b border-base-700 pb-2 text-xs">
        {MESSAGING_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`rounded px-2 py-1 font-medium ${
              activeTab === tab ? "bg-accent-500/20 text-accent-400" : "text-slate-400 hover:bg-base-800"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="mb-2 flex-1 space-y-1 overflow-auto text-xs">
        {activeTab === "APRS" && aprsPackets.length > 0
          ? aprsPackets.map((event) => {
              const latitude = event.data.latitude;
              const longitude = event.data.longitude;
              const hasPosition = typeof latitude === "number" && typeof longitude === "number";
              return (
                <div key={event.id} className="flex gap-2">
                  <span className="shrink-0 text-slate-500">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="shrink-0 font-medium text-accent-400">
                    {String(event.data.source ?? "?")}
                  </span>
                  <span className="truncate text-slate-300">{String(event.data.info ?? "")}</span>
                  {hasPosition && (
                    <span className="shrink-0 font-mono text-slate-500">
                      {latitude.toFixed(4)}, {longitude.toFixed(4)}
                    </span>
                  )}
                </div>
              );
            })
          : SAMPLE_APRS_MESSAGES.map((message, index) => (
              <div key={index} className="flex gap-2">
                <span className="shrink-0 text-slate-500">{message.time}</span>
                <span className="shrink-0 font-medium text-accent-400">{message.from}</span>
                <span className="truncate text-slate-300">{message.text}</span>
              </div>
            ))}
      </div>

      <form
        onSubmit={(event) => event.preventDefault()}
        className="flex gap-2 border-t border-base-700 pt-2"
      >
        <input
          disabled
          placeholder="Test message from Echo Base!"
          className="w-full rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-300 placeholder:text-slate-600"
        />
        <button
          type="submit"
          disabled
          className="cursor-not-allowed rounded-md bg-accent-500/20 px-3 py-1 text-xs text-accent-400"
        >
          Send
        </button>
      </form>
    </Panel>
  );
}
