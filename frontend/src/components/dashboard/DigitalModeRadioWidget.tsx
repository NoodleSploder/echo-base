import { useState } from "react";
import { Panel } from "../common/Panel";
import { DIGITAL_MODE_TABS, SAMPLE_DMR_DECODE } from "../../lib/sampleData";

export function DigitalModeRadioWidget() {
  const [activeTab, setActiveTab] = useState("DMR");
  const decode = SAMPLE_DMR_DECODE;

  return (
    <Panel title="Digital Mode Radio" sample bodyClassName="p-3">
      <div className="mb-3 flex flex-wrap gap-1 border-b border-base-700 pb-2 text-xs">
        {DIGITAL_MODE_TABS.map((tab) => (
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

      <div className="mb-2 text-sm font-semibold text-slate-100">{decode.talkgroup}</div>
      <div className="mb-3 text-xs text-slate-500">{decode.source}</div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <span className="text-slate-400">Source</span>
        <span className="text-right text-slate-200">Time</span>
        <span className="text-slate-200">{decode.callsign}</span>
        <span className="text-right text-slate-200">{decode.time}</span>

        <span className="text-slate-400">Duration</span>
        <span className="text-right text-slate-200">{decode.duration}</span>

        <span className="text-slate-400">BER</span>
        <span className="text-right text-amber-400">{decode.ber}</span>
        <span className="text-slate-400">RSSI</span>
        <span className="text-right text-slate-200">{decode.rssi}</span>
        <span className="text-slate-400">SNR</span>
        <span className="text-right text-slate-200">{decode.snr}</span>

        <span className="text-slate-400">Call Type</span>
        <span className="text-right text-slate-200">{decode.callType}</span>
        <span className="text-slate-400">Encryption</span>
        <span className="text-right text-slate-200">{decode.encryption}</span>
      </div>

      <div className="mt-3 flex h-6 items-end gap-0.5">
        {Array.from({ length: 40 }, (_, i) => (
          <span
            key={i}
            style={{ height: `${20 + Math.abs(Math.sin(i / 3)) * 80}%` }}
            className="w-1 flex-1 rounded-sm bg-accent-400/70"
          />
        ))}
      </div>
    </Panel>
  );
}
