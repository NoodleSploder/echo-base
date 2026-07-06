import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/apiClient";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-base-950 px-4">
      <form
        onSubmit={(event) => void handleSubmit(event)}
        className="w-full max-w-sm space-y-4 rounded-lg border border-base-700 bg-base-900/70 p-8 shadow-xl"
      >
        <div className="text-center">
          <div className="mx-auto mb-2 h-3 w-3 rounded-full bg-accent-400 shadow shadow-accent-400/50" />
          <h1 className="text-xl font-bold text-slate-100">Echo Base</h1>
          <p className="text-sm text-slate-500">Radio Operations Platform</p>
        </div>

        {error && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}

        <div className="space-y-1">
          <label className="text-xs font-medium uppercase tracking-wide text-slate-400">Username</label>
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoFocus
            className="w-full rounded-md border border-base-600 bg-base-800 px-3 py-2 text-slate-100"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium uppercase tracking-wide text-slate-400">Password</label>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-md border border-base-600 bg-base-800 px-3 py-2 text-slate-100"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-accent-500/90 px-3 py-2 font-medium text-base-950 hover:bg-accent-400 disabled:opacity-50"
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
