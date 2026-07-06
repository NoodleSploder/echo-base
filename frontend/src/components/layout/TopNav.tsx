import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useEventStreamContext } from "../../context/EventStreamContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/receivers", label: "Receivers", end: false },
  { to: "/spectrum", label: "Spectrum", end: false },
  { to: "/digital-modes", label: "Digital Modes", end: false },
  { to: "/messaging", label: "Messaging", end: false },
  { to: "/map", label: "Map", end: false },
  { to: "/alerts", label: "Alerts", end: false },
  { to: "/logs", label: "Logs", end: false },
  { to: "/system", label: "System", end: false },
];

export function TopNav() {
  const { user, logout } = useAuth();
  const { connected } = useEventStreamContext();
  const [menuOpen, setMenuOpen] = useState(false);
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex shrink-0 items-center gap-6 border-b border-base-700 bg-base-900/80 px-4 py-2">
      <div className="flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-accent-400" : "bg-slate-600"} shadow shadow-accent-400/50`} />
        <div className="leading-tight">
          <div className="text-sm font-bold tracking-wide text-slate-100">ECHO BASE</div>
          <div className="text-[10px] uppercase tracking-widest text-slate-500">Radio Operations Platform</div>
        </div>
      </div>

      <nav className="flex flex-1 flex-wrap gap-1 text-xs">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `rounded-md px-3 py-1.5 font-medium transition-colors ${
                isActive ? "bg-accent-500/15 text-accent-400" : "text-slate-400 hover:bg-base-800 hover:text-slate-100"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="flex items-center gap-4 text-xs text-slate-400">
        <div className="text-right leading-tight">
          <div className="text-[10px] uppercase tracking-wide text-slate-500">Server Time</div>
          <div className="font-mono text-slate-300">{now.toISOString().replace("T", " ").slice(0, 19)} UTC</div>
        </div>

        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-base-800 text-slate-300 hover:bg-base-700"
            title={user ? `${user.username} (${user.role})` : "Account"}
          >
            {user?.username.slice(0, 1).toUpperCase() ?? "?"}
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-10 z-20 w-48 rounded-md border border-base-700 bg-base-900 p-2 text-xs shadow-xl">
              <div className="border-b border-base-700 px-2 pb-2 text-slate-300">
                {user?.username} <span className="text-slate-500">({user?.role})</span>
              </div>
              <button
                type="button"
                onClick={() => void logout()}
                className="mt-2 w-full rounded-md px-2 py-1.5 text-left text-slate-300 hover:bg-base-800"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
