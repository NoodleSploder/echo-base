import { Panel } from "../common/Panel";
import { SpectrumCanvas } from "../common/SpectrumCanvas";

export function SpectrumOverviewWidget() {
  return (
    <Panel
      title="Spectrum Overview"
      sample
      bodyClassName="p-2"
      actions={
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>Span: 1.8 GHz</span>
          <button type="button" disabled className="rounded border border-base-600 px-1.5 text-slate-500">
            &minus;
          </button>
          <button type="button" disabled className="rounded border border-base-600 px-1.5 text-slate-500">
            +
          </button>
        </div>
      }
    >
      <SpectrumCanvas height={260} />
    </Panel>
  );
}
