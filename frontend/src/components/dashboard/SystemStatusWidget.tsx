import { useEffect, useState } from "react";
import { getHealth, getSystemInfo } from "../../api/system";
import type { HealthStatus, SystemInfo } from "../../types";
import { Panel } from "../common/Panel";
import { Sparkline } from "../common/Sparkline";

// CPU/memory trend, disk, and network are sample data -- the backend
// only exposes process-level metrics today (GET /api/system/metrics),
// not host-wide disk/network stats. Uptime and plugin count are real.
function randomSeries(base: number, spread: number, points = 20): number[] {
  return Array.from({ length: points }, () => Math.max(0, Math.min(100, base + (Math.random() - 0.5) * spread)));
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}d ${hours}h ${minutes}m`;
}

export function SystemStatusWidget() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [cpuSeries] = useState(() => randomSeries(23, 10));
  const [memSeries] = useState(() => randomSeries(41, 8));
  const [diskSeries] = useState(() => randomSeries(62, 4));

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [h, i] = await Promise.all([getHealth(), getSystemInfo()]);
        if (!cancelled) {
          setHealth(h);
          setInfo(i);
        }
      } catch {
        // Leave stale values in place; HealthWidget on the dashboard
        // already surfaces connectivity errors prominently.
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
    <Panel title="System Status" bodyClassName="space-y-3 p-3">
      <Row label="CPU" value="23%" series={cpuSeries} color="#38bdf8" sample />
      <Row label="Memory" value="41%" series={memSeries} color="#a78bfa" sample />
      <Row label="Disk" value="62%" series={diskSeries} color="#fb923c" sample />
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">Network</span>
        <span className="font-mono text-slate-200">
          <span className="text-emerald-400">&uarr;</span> 42.3 <span className="text-slate-500">Mbps</span>{" "}
          <span className="text-sky-400">&darr;</span> 18.7 <span className="text-slate-500">Mbps</span>
        </span>
      </div>
      <div className="border-t border-base-700 pt-2 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Uptime</span>
          <span className="font-mono text-slate-200">{info ? formatUptime(info.uptime_seconds) : "-"}</span>
        </div>
        <div className="mt-1 flex items-center justify-between">
          <span className="text-slate-400">Plugins loaded</span>
          <span className="font-mono text-slate-200">{health ? health.plugins_loaded : "-"}</span>
        </div>
      </div>
    </Panel>
  );
}

function Row({
  label,
  value,
  series,
  color,
  sample,
}: {
  label: string;
  value: string;
  series: number[];
  color: string;
  sample?: boolean;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 text-slate-400">
          {label}
          {sample && <span className="text-[9px] uppercase text-amber-500">sample</span>}
        </span>
        <span className="font-mono text-slate-200">{value}</span>
      </div>
      <Sparkline data={series} stroke={color} className="h-6 w-full" />
    </div>
  );
}
