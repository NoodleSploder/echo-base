import { SAMPLE_RECEIVERS, SAMPLE_RECORDINGS } from "../../lib/sampleData";

// Mirrors the fixed sample percentages shown in SystemStatusWidget so
// the two don't visually disagree; both are clearly-labeled samples.
export function BottomStatusBar() {
  return (
    <footer className="flex shrink-0 flex-wrap items-center gap-x-6 gap-y-1 border-t border-base-700 bg-base-900/80 px-4 py-1.5 text-[11px] text-slate-400">
      <span>
        <span className="text-emerald-400">&#9679;</span> {SAMPLE_RECEIVERS.length} Receivers Online
      </span>
      <span>{SAMPLE_RECORDINGS.length} Recordings</span>
      <span>0 Errors</span>
      <span>CPU: 23%</span>
      <span>MEM: 41%</span>
      <span>NET: 42.3 Mbps</span>
      <span className="ml-auto text-amber-500">Sample data shown for panels without a backend yet</span>
    </footer>
  );
}
