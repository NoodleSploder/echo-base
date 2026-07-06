const COLORS: Record<string, string> = {
  ok: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  connected: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  streaming: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  idle: "bg-slate-500/15 text-slate-300 ring-slate-500/30",
  degraded: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
  disabled: "bg-slate-500/15 text-slate-400 ring-slate-500/30",
  error: "bg-red-500/15 text-red-400 ring-red-500/30",
  disconnected: "bg-red-500/15 text-red-400 ring-red-500/30",
};

export function StatusBadge({ status }: { status: string }) {
  const classes = COLORS[status] ?? "bg-slate-500/15 text-slate-300 ring-slate-500/30";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${classes}`}>
      {status}
    </span>
  );
}
