import { Panel } from "../common/Panel";
import { MiniWaterfall } from "../common/MiniWaterfall";
import { SAMPLE_RECEIVERS } from "../../lib/sampleData";

export function ReceiverTileGridWidget() {
  return (
    <Panel title="Receiver Tiles" sample bodyClassName="p-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {SAMPLE_RECEIVERS.map((receiver, index) => (
          <div key={receiver.id} className="rounded-md border border-base-700 bg-base-800/40 p-2">
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <span className={`h-1.5 w-1.5 rounded-full ${receiver.colorClass}`} />
                {receiver.label} {receiver.name}
              </span>
              <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400">
                ONLINE
              </span>
            </div>
            <div className="mb-1 font-mono text-lg text-slate-100">{receiver.freqMhz.toFixed(3)} MHz</div>
            <MiniWaterfall height={56} colorSeed={index * 3} />
            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-slate-400">
              {Object.entries(receiver.detail).map(([key, value]) => (
                <span key={key}>
                  {key} <span className="text-slate-200">{value}</span>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
