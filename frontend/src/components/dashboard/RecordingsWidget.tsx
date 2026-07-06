import { useEffect, useState } from "react";
import {
  deleteRecording,
  listRecordings,
  recordingDownloadUrl,
  startPlayback,
  stopPlayback,
} from "../../api/recordings";
import { useSpectrumStream } from "../../hooks/useWebSocket";
import type { RecordingInfo } from "../../types";
import { SpectrumCanvas } from "../common/SpectrumCanvas";
import { Panel } from "../common/Panel";
import { SAMPLE_RECORDINGS } from "../../lib/sampleData";

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Real data: GET /api/recordings -- files written by RecordingService
// when "Record Audio"/"Record" is toggled on a receiver (see
// ReceiverCard). Raw ".iq" recordings can additionally be "played back"
// through the real spectrum pipeline (see StreamService.register_playback).
export function RecordingsWidget() {
  const [recordings, setRecordings] = useState<RecordingInfo[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [deletingFilename, setDeletingFilename] = useState<string | null>(null);
  const [playingFilename, setPlayingFilename] = useState<string | null>(null);
  const [playbackId, setPlaybackId] = useState<string | null>(null);
  const [playingAudioFilename, setPlayingAudioFilename] = useState<string | null>(null);
  const { frame, connected } = useSpectrumStream(playbackId);

  async function refresh() {
    try {
      const found = await listRecordings();
      setRecordings(found);
    } catch {
      // Leave prior state in place; System Status widget already
      // surfaces backend connectivity problems prominently.
    } finally {
      setLoaded(true);
    }
  }

  useEffect(() => {
    void refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, []);

  async function stopCurrentPlayback() {
    if (playingFilename) {
      await stopPlayback(playingFilename);
    }
    setPlayingFilename(null);
    setPlaybackId(null);
  }

  async function handleTogglePlay(filename: string) {
    if (playingFilename === filename) {
      await stopCurrentPlayback();
      return;
    }
    await stopCurrentPlayback();
    const { playback_id } = await startPlayback(filename);
    setPlayingFilename(filename);
    setPlaybackId(playback_id);
  }

  async function handleDelete(filename: string) {
    setDeletingFilename(filename);
    try {
      if (playingFilename === filename) await stopCurrentPlayback();
      if (playingAudioFilename === filename) setPlayingAudioFilename(null);
      await deleteRecording(filename);
      await refresh();
    } finally {
      setDeletingFilename(null);
    }
  }

  function handleToggleAudio(filename: string) {
    setPlayingAudioFilename((prev) => (prev === filename ? null : filename));
  }

  const hasRealRecordings = recordings.length > 0;

  return (
    <Panel title="Recordings" sample={!hasRealRecordings} bodyClassName="p-2">
      <table className="w-full text-left text-xs">
        <thead className="text-slate-500">
          <tr>
            <th className="pb-1 font-medium">Recorder</th>
            <th className="pb-1 font-medium">Freq</th>
            <th className="pb-1 font-medium">Start</th>
            <th className="pb-1 font-medium">Duration</th>
            <th className="pb-1 font-medium">Size</th>
            {hasRealRecordings && <th className="pb-1 font-medium" />}
          </tr>
        </thead>
        <tbody>
          {hasRealRecordings
            ? recordings.map((recording) => (
                <tr key={recording.filename} className="border-t border-base-800">
                  <td className="py-1 text-slate-200">
                    {recording.active && <span className="mr-1 text-red-400">●</span>}
                    {recording.active ? (
                      recording.receiver_id
                    ) : (
                      <a
                        href={recordingDownloadUrl(recording.filename)}
                        className="text-accent-400 hover:underline"
                      >
                        {recording.receiver_id}
                      </a>
                    )}
                  </td>
                  <td className="py-1 text-slate-400">
                    {recording.frequency_hz ? `${(recording.frequency_hz / 1e6).toFixed(3)} MHz` : "--"}
                  </td>
                  <td className="py-1 text-slate-400">{recording.started_at}</td>
                  <td className="py-1 text-slate-400">{formatDuration(recording.duration_seconds)}</td>
                  <td className="py-1 text-slate-400">{formatSize(recording.size_bytes)}</td>
                  <td className="py-1 text-right whitespace-nowrap">
                    {!recording.active && recording.mode === "iq" && (
                      <button
                        type="button"
                        onClick={() => void handleTogglePlay(recording.filename)}
                        className="mr-2 text-slate-500 hover:text-accent-400"
                        title="Play back through the spectrum pipeline"
                      >
                        {playingFilename === recording.filename ? "■" : "▶"}
                      </button>
                    )}
                    {!recording.active && recording.mode !== "iq" && (
                      <button
                        type="button"
                        onClick={() => handleToggleAudio(recording.filename)}
                        className="mr-2 text-slate-500 hover:text-accent-400"
                        title="Play audio"
                      >
                        {playingAudioFilename === recording.filename ? "■" : "▶"}
                      </button>
                    )}
                    {!recording.active && (
                      <button
                        type="button"
                        onClick={() => void handleDelete(recording.filename)}
                        disabled={deletingFilename === recording.filename}
                        className="text-slate-500 hover:text-red-400 disabled:opacity-50"
                        title="Delete recording"
                      >
                        &times;
                      </button>
                    )}
                  </td>
                </tr>
              ))
            : loaded &&
              SAMPLE_RECORDINGS.map((recording) => (
                <tr key={recording.id} className="border-t border-base-800">
                  <td className="py-1 text-slate-200">{recording.recorder}</td>
                  <td className="py-1 text-slate-400">{recording.freq}</td>
                  <td className="py-1 text-slate-400">{recording.start}</td>
                  <td className="py-1 text-slate-400">{recording.duration}</td>
                  <td className="py-1 text-slate-400">{recording.size}</td>
                </tr>
              ))}
        </tbody>
      </table>
      {!hasRealRecordings && (
        <button
          type="button"
          disabled
          className="mt-2 w-full cursor-not-allowed rounded-md border border-base-600 py-1.5 text-xs text-slate-500"
        >
          View All Recordings
        </button>
      )}
      {playingFilename && (
        <div className="mt-2 rounded-md border border-base-700 bg-base-800/40 p-2">
          <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
            <span>
              Playing back <span className="text-slate-200">{playingFilename}</span>
            </span>
            <span>{connected ? "streaming" : "loading..."}</span>
          </div>
          <SpectrumCanvas height={80} liveFrame={frame} />
        </div>
      )}
      {playingAudioFilename && (
        <div className="mt-2 rounded-md border border-base-700 bg-base-800/40 p-2">
          <div className="mb-1 text-xs text-slate-400">
            Playing <span className="text-slate-200">{playingAudioFilename}</span>
          </div>
          <audio
            key={playingAudioFilename}
            controls
            autoPlay
            src={recordingDownloadUrl(playingAudioFilename)}
            className="w-full"
            onEnded={() => setPlayingAudioFilename(null)}
          />
        </div>
      )}
    </Panel>
  );
}
