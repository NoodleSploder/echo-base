import { useEffect, useState } from "react";
import { getHealth, getSystemInfo } from "../../api/system";
import type { HealthStatus, SystemInfo } from "../../types";
import { Card } from "../common/Card";
import { StatusBadge } from "../common/StatusBadge";

export function HealthWidget() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [h, i] = await Promise.all([getHealth(), getSystemInfo()]);
        if (!cancelled) {
          setHealth(h);
          setInfo(i);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("Unable to reach the Echo Base API.");
      }
    }

    void load();
    const interval = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <Card title="System Health">
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!error && health && info && (
        <dl className="grid grid-cols-2 gap-y-2 text-sm">
          <dt className="text-slate-400">Status</dt>
          <dd>
            <StatusBadge status={health.status} />
          </dd>
          <dt className="text-slate-400">Database</dt>
          <dd>
            <StatusBadge status={health.database} />
          </dd>
          <dt className="text-slate-400">Plugins loaded</dt>
          <dd className="text-slate-200">{health.plugins_loaded}</dd>
          <dt className="text-slate-400">Version</dt>
          <dd className="text-slate-200">{info.version}</dd>
          <dt className="text-slate-400">Host</dt>
          <dd className="text-slate-200">{info.hostname}</dd>
          <dt className="text-slate-400">Uptime</dt>
          <dd className="text-slate-200">{Math.floor(info.uptime_seconds)}s</dd>
        </dl>
      )}
      {!error && !health && <p className="text-sm text-slate-500">Loading...</p>}
    </Card>
  );
}
