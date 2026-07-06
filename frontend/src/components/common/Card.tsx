import type { ReactNode } from "react";

export function Card({ title, children, actions }: { title?: string; children: ReactNode; actions?: ReactNode }) {
  return (
    <div className="rounded-lg border border-base-700 bg-base-900/60 shadow-lg shadow-black/20">
      {(title || actions) && (
        <div className="flex items-center justify-between border-b border-base-700 px-4 py-3">
          {title && <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">{title}</h2>}
          {actions}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}
