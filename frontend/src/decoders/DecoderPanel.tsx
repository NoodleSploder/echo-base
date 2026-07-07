import { useEffect, useState, type ChangeEvent } from "react";
import { getCaptureHealth, getReceiver, listReceivers, tuneReceiver } from "../api/receivers";
import type { ReceiverDescriptor } from "../types";
import { Card } from "../components/common/Card";
import { isInBand } from "./DecoderRegistry";
import type { DecoderDefinition } from "./types";

const RECEIVER_POLL_MS = 10000;
const HEALTH_POLL_MS = 4000;
const STORAGE_PREFIX = "echo-base:decoder-panel-receiver:";

// The point of this component: a decoder (FT8, ADS-B, ...) is an
// independent, self-contained unit that gets *pointed at* whichever
// receiver you choose, rather than being a feature bolted onto that
// receiver's own card. Each instance remembers its own receiver
// assignment (per decoder id) across reloads, so switching between
// several decoder panels -- each listening on its own receiver/config
// -- is the normal way to use this, not an afterthought.
export function DecoderPanel({ decoder }: { decoder: DecoderDefinition }) {
  const storageKey = STORAGE_PREFIX + decoder.id;
  const [receivers, setReceivers] = useState<ReceiverDescriptor[]>([]);
  const [receiverId, setReceiverId] = useState<string>(() => localStorage.getItem(storageKey) ?? "");
  const [frequencyHz, setFrequencyHz] = useState<number | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [tuning, setTuning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await listReceivers();
        if (!cancelled) setReceivers(data);
      } catch {
        // Transient poll failure; keep showing the last good list.
      }
    }
    void poll();
    const interval = setInterval(poll, RECEIVER_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (!receiverId) {
      setEnabled(false);
      setFrequencyHz(null);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const [health, status] = await Promise.all([getCaptureHealth(receiverId), getReceiver(receiverId)]);
        if (cancelled) return;
        const value = health[decoder.healthKey];
        if (typeof value === "boolean") setEnabled(value);
        setFrequencyHz(status.frequency_hz ?? null);
      } catch {
        // Transient poll failure (or the receiver disappeared); keep
        // showing the last good reading rather than flipping state.
      }
    }
    void poll();
    const interval = setInterval(poll, HEALTH_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [receiverId, decoder.healthKey]);

  function handleReceiverChange(next: string) {
    setReceiverId(next);
    if (next) localStorage.setItem(storageKey, next);
    else localStorage.removeItem(storageKey);
  }

  async function handleBandChange(event: ChangeEvent<HTMLSelectElement>) {
    const hz = Number(event.target.value);
    if (!receiverId || !Number.isFinite(hz) || hz <= 0) return;
    setTuning(true);
    try {
      const status = await tuneReceiver(receiverId, hz);
      setFrequencyHz(status.frequency_hz ?? hz);
    } finally {
      setTuning(false);
    }
  }

  async function handleToggle() {
    if (!receiverId) return;
    setBusy(true);
    try {
      if (enabled) {
        await decoder.stop(receiverId);
      } else {
        await decoder.start(receiverId);
      }
      setEnabled((prev) => !prev);
    } finally {
      setBusy(false);
    }
  }

  const inBand = isInBand(decoder, frequencyHz);
  const Panel = decoder.Panel;

  return (
    <Card title={decoder.name}>
      <div className="space-y-2 text-sm">
        <p className="text-xs text-slate-500">{decoder.description}</p>
        {decoder.feedsMapLayer && (
          <p className="text-[11px] text-accent-400">Feeds the Geospatial map when enabled.</p>
        )}

        <div className="flex gap-2">
          <select
            value={receiverId}
            onChange={(event) => handleReceiverChange(event.target.value)}
            disabled={enabled}
            className="min-w-0 flex-1 rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-200 disabled:opacity-50"
          >
            <option value="">Select a receiver...</option>
            {receivers.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        {decoder.bands.length > 0 && (
          <select
            value={decoder.bands.find((band) => band.hz === frequencyHz)?.hz ?? ""}
            onChange={(event) => void handleBandChange(event)}
            disabled={!receiverId || enabled || tuning}
            title="Tune the selected receiver to one of this decoder's standard frequencies"
            className="w-full rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-200 disabled:opacity-50"
          >
            <option value="" disabled>
              {tuning ? "Tuning..." : "Tune to band..."}
            </option>
            {decoder.bands.map((band) => (
              <option key={band.label} value={band.hz}>
                {band.label}
              </option>
            ))}
          </select>
        )}

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void handleToggle()}
            disabled={busy || !receiverId}
            title={
              receiverId && !inBand
                ? "Outside this decoder's typical frequency range for the receiver's current tuning"
                : undefined
            }
            className={`shrink-0 rounded-md px-3 py-1 text-xs font-medium disabled:opacity-50 ${
              enabled
                ? "bg-accent-500/20 text-accent-400 hover:bg-accent-500/30"
                : "border border-base-600 text-slate-300 hover:bg-base-800"
            } ${receiverId && !inBand ? "opacity-60" : ""}`}
          >
            {enabled ? "Stop" : "Start"}
          </button>
        </div>

        {receiverId && frequencyHz !== null && !inBand && (
          <p className="text-[11px] text-amber-500">
            Tuned to {(frequencyHz / 1e6).toFixed(4)}MHz -- outside {decoder.name}'s typical range.
          </p>
        )}

        {receiverId ? (
          Panel ? (
            <div className="border-t border-base-700 pt-2">
              <Panel receiverId={receiverId} />
            </div>
          ) : null
        ) : (
          <p className="text-xs text-slate-500">Pick a receiver to start decoding.</p>
        )}
      </div>
    </Card>
  );
}
