import type { ReactNode } from "react";

// The `drag-handle` class marks the region react-grid-layout should
// treat as the drag handle (see DashboardPage's draggableHandle prop) --
// without it, dragging a widget by its buttons/inputs would be unusable.
export function Panel({
  title,
  children,
  actions,
  sample = false,
  bodyClassName = "p-3",
}: {
  title: string;
  children: ReactNode;
  actions?: ReactNode;
  sample?: boolean;
  bodyClassName?: string;
}) {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-base-700 bg-base-900/70 shadow-lg shadow-black/30">
      <div className="drag-handle flex shrink-0 cursor-move items-center justify-between border-b border-base-700 bg-base-800/60 px-3 py-2">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">{title}</h3>
          {sample && (
            <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-400">
              Sample
            </span>
          )}
        </div>
        {actions}
      </div>
      <div className={`min-h-0 flex-1 overflow-auto ${bodyClassName}`}>{children}</div>
    </div>
  );
}
