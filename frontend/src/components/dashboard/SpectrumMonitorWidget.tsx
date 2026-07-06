import { Panel } from "../common/Panel";
import { SpectrumCanvas } from "../common/SpectrumCanvas";

export function SpectrumMonitorWidget() {
  return (
    <Panel
      title="Spectrum Monitor (R8)"
      sample
      bodyClassName="p-2"
      actions={<span className="text-xs text-slate-500">FFT 16384 &middot; RBW 7.6 kHz</span>}
    >
      <SpectrumCanvas height={160} />
    </Panel>
  );
}
