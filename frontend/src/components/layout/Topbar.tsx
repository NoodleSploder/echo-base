import { useAuth } from "../../context/AuthContext";
import { useEventStreamContext } from "../../context/EventStreamContext";

export function Topbar() {
  const { user, logout } = useAuth();
  const { connected } = useEventStreamContext();

  return (
    <header className="flex items-center justify-between border-b border-base-700 bg-base-900/60 px-6 py-3">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-slate-600"}`} />
        {connected ? "Live" : "Reconnecting..."}
      </div>
      <div className="flex items-center gap-4">
        {user && (
          <span className="text-sm text-slate-300">
            {user.username} <span className="text-slate-500">({user.role})</span>
          </span>
        )}
        <button
          onClick={() => void logout()}
          className="rounded-md border border-base-600 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-base-800"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
