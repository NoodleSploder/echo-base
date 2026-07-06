import { useEffect, useState, type FormEvent } from "react";
import {
  getCaptureHealth,
  getOccupancy,
  getSignalHistory,
  startAprsDecoding,
  startOccupancy,
  startReceiver,
  startSameDecoding,
  startSignalDetection,
  stopAprsDecoding,
  stopOccupancy,
  stopReceiver,
  stopSameDecoding,
  stopSignalDetection,
  tuneReceiver,
} from "../../api/receivers";
import { startRecording, stopRecording } from "../../api/recordings";
import { useAudioPlayer } from "../../hooks/useAudioPlayer";
import type { ReceiverDescriptor, ReceiverStatus } from "../../types";
import { Card } from "../common/Card";
import { StatusBadge } from "../common/StatusBadge";

// Matches backend/app/services/dsp.py's DEMODULATORS -- USB/LSB (SSB)
// demod isn't implemented in software yet, so only FM/AM are offered.
const AUDIO_MODES = ["fm", "am"];
// Recording additionally offers "iq" (raw samples, not demodulated) --
// not a Listen option since there's nothing to play back live for it.
const RECORDING_MODES = ["fm", "am", "iq"];

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
  const [listening, setListening] = useState(false);
  const [mode, setMode] = useState("fm");
  const [squelch, setSquelch] = useState(0);
  const [aprsEnabled, setAprsEnabled] = useState(false);
  const [aprsBusy, setAprsBusy] = useState(false);
  const [sameEnabled, setSameEnabled] = useState(false);
  const [sameBusy, setSameBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordingBusy, setRecordingBusy] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [recordingMode, setRecordingMode] = useState("fm");
  const [signalDetectionEnabled, setSignalDetectionEnabled] = useState(false);
  const [signalDetectionBusy, setSignalDetectionBusy] = useState(false);
  const [marginDb, setMarginDb] = useState(15);
  const [occupancyEnabled, setOccupancyEnabled] = useState(false);
  const [occupancyBusy, setOccupancyBusy] = useState(false);
  const [occupancySummary, setOccupancySummary] = useState<{ avgPercent: number; peakFrequencyHz: number } | null>(
    null,
  );
  const [historyCount, setHistoryCount] = useState<number | null>(null);
  const [captureStalled, setCaptureStalled] = useState(false);

  const state = status?.state ?? "idle";
  // Audio is derived from the same IQ capture as the spectrum widgets
  // (see StreamService), so any receiver with IQ streaming gets Listen.
  const supportsAudio = receiver.capabilities.iq_streaming === true;
  const { connected: audioConnected, level } = useAudioPlayer(receiver.id, mode, listening, squelch);
  const meterWidth = Math.min(1, level * 2.5) * 100;

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

  async function handleToggleAprs() {
    setAprsBusy(true);
    try {
      if (aprsEnabled) {
        await stopAprsDecoding(receiver.id);
      } else {
        await startAprsDecoding(receiver.id);
      }
      setAprsEnabled((prev) => !prev);
    } finally {
      setAprsBusy(false);
    }
  }

  async function handleToggleSame() {
    setSameBusy(true);
    try {
      if (sameEnabled) {
        await stopSameDecoding(receiver.id);
      } else {
        await startSameDecoding(receiver.id);
      }
      setSameEnabled((prev) => !prev);
    } finally {
      setSameBusy(false);
    }
  }

  async function handleToggleSignalDetection() {
    setSignalDetectionBusy(true);
    try {
      if (signalDetectionEnabled) {
        await stopSignalDetection(receiver.id);
      } else {
        await startSignalDetection(receiver.id, marginDb);
        setHistoryCount(null);
      }
      setSignalDetectionEnabled((prev) => !prev);
    } finally {
      setSignalDetectionBusy(false);
    }
  }

  useEffect(() => {
    if (!signalDetectionEnabled) return;
    let cancelled = false;
    async function poll() {
      try {
        const records = await getSignalHistory(receiver.id, 60);
        if (!cancelled) setHistoryCount(records.length);
      } catch {
        // Transient poll failure; keep showing the last good count.
      }
    }
    void poll();
    const interval = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [signalDetectionEnabled, receiver.id]);

  async function handleToggleOccupancy() {
    setOccupancyBusy(true);
    try {
      if (occupancyEnabled) {
        await stopOccupancy(receiver.id);
        setOccupancySummary(null);
      } else {
        await startOccupancy(receiver.id, marginDb);
      }
      setOccupancyEnabled((prev) => !prev);
    } finally {
      setOccupancyBusy(false);
    }
  }

  useEffect(() => {
    if (!occupancyEnabled) return;
    let cancelled = false;
    async function poll() {
      try {
        const snapshot = await getOccupancy(receiver.id);
        if (cancelled) return;
        const avgPercent =
          snapshot.occupancy_percent.reduce((sum, v) => sum + v, 0) / snapshot.occupancy_percent.length;
        const peakIndex = snapshot.occupancy_percent.reduce(
          (best, v, i) => (v > snapshot.occupancy_percent[best] ? i : best),
          0,
        );
        setOccupancySummary({ avgPercent, peakFrequencyHz: snapshot.frequencies_hz[peakIndex] });
      } catch {
        // Transient poll failure; keep showing the last good reading.
      }
    }
    void poll();
    const interval = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [occupancyEnabled, receiver.id]);

  const captureShouldBeActive =
    listening || recording || aprsEnabled || sameEnabled || signalDetectionEnabled || occupancyEnabled;

  useEffect(() => {
    if (!captureShouldBeActive) {
      setCaptureStalled(false);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const health = await getCaptureHealth(receiver.id);
        if (cancelled) return;
        const stalled =
          health.active &&
          (health.alive === false ||
            (typeof health.last_read_age_seconds === "number" && health.last_read_age_seconds > 3));
        setCaptureStalled(stalled);
      } catch {
        // Transient poll failure; don't flip the badge on a single miss.
      }
    }
    void poll();
    const interval = setInterval(poll, 4000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [captureShouldBeActive, receiver.id]);

  async function handleToggleRecording() {
    setRecordingBusy(true);
    setRecordingError(null);
    try {
      if (recording) {
        await stopRecording(receiver.id);
      } else {
        await startRecording(receiver.id, recordingMode);
      }
      setRecording((prev) => !prev);
    } catch {
      setRecordingError("Could not toggle recording.");
    } finally {
      setRecordingBusy(false);
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

        {captureStalled && (
          <p
            className="rounded-md bg-red-500/10 px-2 py-1 text-xs text-red-400"
            title="The capture feeding Listen/Record/decoders has stopped producing samples. Toggling a feature off and back on restarts it."
          >
            Capture stalled -- no samples received recently
          </p>
        )}

        {supportsAudio && (
          <div className="flex items-center gap-2 border-t border-base-700 pt-3">
            <select
              value={mode}
              onChange={(event) => setMode(event.target.value)}
              disabled={listening}
              className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-300 disabled:opacity-50"
            >
              {AUDIO_MODES.map((m) => (
                <option key={m} value={m}>
                  {m.toUpperCase()}
                </option>
              ))}
            </select>
            <button
              onClick={() => setListening((prev) => !prev)}
              className={`flex-1 rounded-md py-1.5 text-xs font-medium ${
                listening
                  ? "bg-accent-500/20 text-accent-400 hover:bg-accent-500/30"
                  : "border border-base-600 text-slate-300 hover:bg-base-800"
              }`}
            >
              {listening ? (audioConnected ? "Listening..." : "Connecting...") : "Listen"}
            </button>
          </div>
        )}

        {supportsAudio && listening && (
          <div className="space-y-2 text-xs">
            <div>
              <div className="mb-1 flex items-center justify-between text-slate-400">
                <span>Level</span>
                {squelch > 0 && level < squelch && <span className="text-amber-500">squelched</span>}
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-base-800">
                <div
                  className={`h-full rounded-full transition-[width] duration-75 ${
                    squelch > 0 && level < squelch ? "bg-slate-600" : "bg-emerald-400"
                  }`}
                  style={{ width: `${meterWidth}%` }}
                />
              </div>
            </div>
            <label className="flex items-center gap-2 text-slate-400">
              <span className="shrink-0">Squelch</span>
              <input
                type="range"
                min={0}
                max={0.3}
                step={0.005}
                value={squelch}
                onChange={(event) => setSquelch(Number(event.target.value))}
                className="w-full"
              />
            </label>
          </div>
        )}

        {supportsAudio && (
          <div className="flex gap-2 border-t border-base-700 pt-3">
            <button
              onClick={() => void handleToggleAprs()}
              disabled={aprsBusy}
              className={`flex-1 rounded-md py-1.5 text-xs font-medium disabled:opacity-50 ${
                aprsEnabled
                  ? "bg-accent-500/20 text-accent-400 hover:bg-accent-500/30"
                  : "border border-base-600 text-slate-300 hover:bg-base-800"
              }`}
              title="Decoded APRS packets appear in the Activity Feed, System Log, and Messaging Center widgets"
            >
              {aprsEnabled ? "APRS Decoding On" : "Decode APRS"}
            </button>
            <button
              onClick={() => void handleToggleSame()}
              disabled={sameBusy}
              className={`flex-1 rounded-md py-1.5 text-xs font-medium disabled:opacity-50 ${
                sameEnabled
                  ? "bg-accent-500/20 text-accent-400 hover:bg-accent-500/30"
                  : "border border-base-600 text-slate-300 hover:bg-base-800"
              }`}
              title="Decoded NOAA Weather Radio SAME alerts appear in the Activity Feed, System Log, and Alerts widgets"
            >
              {sameEnabled ? "SAME Decoding On" : "Decode SAME"}
            </button>
          </div>
        )}

        {supportsAudio && (
          <div className="flex items-center gap-2 border-t border-base-700 pt-3">
            <input
              type="number"
              value={marginDb}
              onChange={(event) => setMarginDb(Number(event.target.value))}
              disabled={signalDetectionEnabled}
              step={5}
              className="w-16 rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-300 disabled:opacity-50"
              title="dB above the noise floor required to count as a signal"
            />
            <button
              onClick={() => void handleToggleSignalDetection()}
              disabled={signalDetectionBusy}
              className={`flex-1 rounded-md py-1.5 text-xs font-medium disabled:opacity-50 ${
                signalDetectionEnabled
                  ? "bg-accent-500/20 text-accent-400 hover:bg-accent-500/30"
                  : "border border-base-600 text-slate-300 hover:bg-base-800"
              }`}
              title="Detected signal peaks appear in the Activity Feed and System Log widgets"
            >
              {signalDetectionEnabled ? "Signal Detection On" : "Detect Signals"}
            </button>
          </div>
        )}
        {signalDetectionEnabled && historyCount !== null && (
          <p className="text-xs text-slate-400">{historyCount} detection(s) in the last hour</p>
        )}

        {supportsAudio && (
          <div className="border-t border-base-700 pt-3">
            <button
              onClick={() => void handleToggleOccupancy()}
              disabled={occupancyBusy}
              className={`w-full rounded-md py-1.5 text-xs font-medium disabled:opacity-50 ${
                occupancyEnabled
                  ? "bg-accent-500/20 text-accent-400 hover:bg-accent-500/30"
                  : "border border-base-600 text-slate-300 hover:bg-base-800"
              }`}
              title="Tracks what fraction of the band has been occupied recently"
            >
              {occupancyEnabled ? "Occupancy Tracking On" : "Track Occupancy"}
            </button>
            {occupancySummary && (
              <p className="mt-1 text-xs text-slate-400">
                avg {occupancySummary.avgPercent.toFixed(1)}% occupied · busiest{" "}
                {(occupancySummary.peakFrequencyHz / 1e6).toFixed(4)} MHz
              </p>
            )}
          </div>
        )}

        {supportsAudio && (
          <div className="flex items-center gap-2 border-t border-base-700 pt-3">
            <select
              value={recordingMode}
              onChange={(event) => setRecordingMode(event.target.value)}
              disabled={recording}
              className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-300 disabled:opacity-50"
            >
              {RECORDING_MODES.map((m) => (
                <option key={m} value={m}>
                  {m.toUpperCase()}
                </option>
              ))}
            </select>
            <button
              onClick={() => void handleToggleRecording()}
              disabled={recordingBusy}
              className={`flex-1 rounded-md py-1.5 text-xs font-medium disabled:opacity-50 ${
                recording
                  ? "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                  : "border border-base-600 text-slate-300 hover:bg-base-800"
              }`}
              title={
                recordingMode === "iq"
                  ? "Records raw IQ samples to a .iq file -- see the Recordings widget"
                  : `Records the current "${recordingMode.toUpperCase()}" audio to a WAV file -- see the Recordings widget`
              }
            >
              {recording ? "● Recording..." : "Record"}
            </button>
          </div>
        )}
        {recordingError && <p className="text-xs text-red-400">{recordingError}</p>}
      </div>
    </Card>
  );
}
