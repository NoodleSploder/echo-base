import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/receivers", label: "Receivers", end: false },
];

const COMING_SOON = ["Radios", "Messaging", "Recording", "Automation", "Maps"];

export function Sidebar() {
  return (
    <aside className="flex w-56 flex-col border-r border-base-700 bg-base-900/80 p-4">
      <div className="mb-6 flex items-center gap-2 px-2">
        <span className="h-2.5 w-2.5 rounded-full bg-accent-400 shadow shadow-accent-400/50" />
        <span className="text-lg font-bold tracking-tight text-slate-100">Echo Base</span>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? "bg-accent-500/10 text-accent-400" : "text-slate-300 hover:bg-base-800 hover:text-slate-100"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
        <div className="mt-4 border-t border-base-700 pt-4">
          <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Coming soon</p>
          {COMING_SOON.map((label) => (
            <div key={label} className="cursor-not-allowed rounded-md px-3 py-2 text-sm text-slate-600">
              {label}
            </div>
          ))}
        </div>
      </nav>
    </aside>
  );
}
