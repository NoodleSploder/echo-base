import { useState, type FormEvent } from "react";
import { startReceiver, stopReceiver, tuneReceiver } from "../../api/receivers";
import type { ReceiverDescriptor, ReceiverStatus } from "../../types";
import { Card } from "../common/Card";
import { StatusBadge } from "../common/StatusBadge";

export function ReceiverCard({
  receiver,
  status,
  onChange,
}: {
  receiver: ReceiverDescriptor;
  status: ReceiverStatus | undefined;
  onChange: (status: ReceiverStatus) => void;
}) {
  const [frequency, setFrequency] = useState("");
  const [busy, setBusy] = useState(false);

  const state = status?.state ?? "idle";

  async function handleStart() {
    setBusy(true);
    try {
      onChange(await startReceiver(receiver.id));
    } finally {
      setBusy(false);
    }
  }

  async function handleStop() {
    setBusy(true);
    try {
      onChange(await stopReceiver(receiver.id));
    } finally {
      setBusy(false);
    }
  }

  async function handleTune(event: FormEvent) {
    event.preventDefault();
    const hz = Number(frequency);
    if (!Number.isFinite(hz) || hz <= 0) return;
    setBusy(true);
    try {
      onChange(await tuneReceiver(receiver.id, hz));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title={receiver.name} actions={<StatusBadge status={state} />}>
      <div className="space-y-3 text-sm">
        <div className="grid grid-cols-2 gap-y-1 text-slate-400">
          <span>Driver</span>
          <span className="text-slate-200">{receiver.driver}</span>
          <span>Frequency</span>
          <span className="text-slate-200">
            {status?.frequency_hz ? `${(status.frequency_hz / 1e6).toFixed(4)} MHz` : "-"}
          </span>
          <span>Sample rate</span>
          <span className="text-slate-200">
            {status?.sample_rate_hz ? `${(status.sample_rate_hz / 1e6).toFixed(3)} MS/s` : "-"}
          </span>
          <span>Gain</span>
          <span className="text-slate-200">{status?.gain ?? "-"}</span>
        </div>

        <form onSubmit={handleTune} className="flex gap-2">
          <input
            type="number"
            placeholder="Frequency (Hz)"
            value={frequency}
            onChange={(event) => setFrequency(event.target.value)}
            className="w-full rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100 placeholder:text-slate-500"
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-accent-500/20 px-3 py-1 text-accent-400 hover:bg-accent-500/30 disabled:opacity-50"
          >
            Tune
          </button>
        </form>

        <div className="flex gap-2">
          <button
            onClick={() => void handleStart()}
            disabled={busy || state === "streaming"}
            className="flex-1 rounded-md bg-emerald-500/15 px-3 py-1.5 text-emerald-400 hover:bg-emerald-500/25 disabled:opacity-40"
          >
            Start
          </button>
          <button
            onClick={() => void handleStop()}
            disabled={busy || state !== "streaming"}
            className="flex-1 rounded-md bg-red-500/15 px-3 py-1.5 text-red-400 hover:bg-red-500/25 disabled:opacity-40"
          >
            Stop
          </button>
        </div>
      </div>
    </Card>
  );
}
