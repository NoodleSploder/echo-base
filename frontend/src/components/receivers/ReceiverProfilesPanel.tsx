import { useEffect, useState, type FormEvent } from "react";
import {
  applyReceiverProfile,
  createReceiverProfile,
  deleteReceiverProfile,
  listReceiverProfiles,
  listSuggestedProfiles,
  type SuggestedReceiverProfile,
} from "../../api/receiverProfiles";
import type { ReceiverDescriptor, ReceiverProfile, ReceiverStatus } from "../../types";
import { Card } from "../common/Card";

// Saved frequency/gain presets a user can apply to any receiver in one
// click, instead of re-typing frequency/gain by hand each time (see
// ROADMAP.md's "Receiver Profiles" Phase 2 item).
export function ReceiverProfilesPanel({
  receivers,
  onApplied,
}: {
  receivers: ReceiverDescriptor[];
  onApplied: (receiverId: string, status: ReceiverStatus) => void;
}) {
  const [profiles, setProfiles] = useState<ReceiverProfile[]>([]);
  const [suggested, setSuggested] = useState<SuggestedReceiverProfile[]>([]);
  const [name, setName] = useState("");
  const [frequencyMhz, setFrequencyMhz] = useState("");
  const [gain, setGain] = useState("");
  const [marginDb, setMarginDb] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function refresh() {
    try {
      setProfiles(await listReceiverProfiles());
    } catch {
      setError("Unable to load receiver profiles.");
    }
  }

  useEffect(() => {
    void refresh();
    void listSuggestedProfiles()
      .then(setSuggested)
      .catch(() => undefined);
  }, []);

  const savedFrequencies = new Set(profiles.map((p) => p.frequency_hz));

  async function handleAddSuggested(preset: SuggestedReceiverProfile) {
    setBusyId(preset.id);
    try {
      await createReceiverProfile({
        name: preset.name,
        frequency_hz: preset.frequency_hz,
        sample_rate_hz: null,
        bandwidth_hz: null,
        gain: preset.gain,
        decoder: preset.decoder,
      });
      setError(null);
      await refresh();
    } catch {
      setError("Unable to save profile.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    const hz = Math.round(Number(frequencyMhz) * 1e6);
    if (!name.trim() || !Number.isFinite(hz) || hz <= 0) return;
    const parsedMargin = marginDb.trim() ? Number(marginDb) : null;
    try {
      await createReceiverProfile({
        name: name.trim(),
        frequency_hz: hz,
        gain: gain.trim() || null,
        margin_db: parsedMargin !== null && Number.isFinite(parsedMargin) ? parsedMargin : null,
      });
      setName("");
      setFrequencyMhz("");
      setGain("");
      setMarginDb("");
      setError(null);
      await refresh();
    } catch {
      setError("Unable to save profile.");
    }
  }

  async function handleDelete(id: string) {
    setBusyId(id);
    try {
      await deleteReceiverProfile(id);
      await refresh();
    } catch {
      setError("Unable to delete profile.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleApply(profileId: string, receiverId: string) {
    if (!receiverId) return;
    setBusyId(profileId);
    try {
      onApplied(receiverId, await applyReceiverProfile(profileId, receiverId));
      setError(null);
    } catch {
      setError("Unable to apply profile.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Card title="Receiver Profiles">
      <div className="space-y-3 text-sm">
        {error && <p className="text-red-400">{error}</p>}

        {profiles.length === 0 && <p className="text-slate-500">No saved profiles yet.</p>}

        <ul className="space-y-2">
          {profiles.map((profile) => (
            <li
              key={profile.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-base-700 bg-base-800/40 px-3 py-2"
            >
              <div>
                <div className="font-medium text-slate-200">{profile.name}</div>
                <div
                  className="text-xs text-slate-500"
                  title={
                    profile.margin_db != null
                      ? "Applying this profile auto-enables signal detection at this margin"
                      : undefined
                  }
                >
                  {(profile.frequency_hz / 1e6).toFixed(4)} MHz
                  {profile.gain ? ` · gain ${profile.gain}` : ""}
                  {profile.margin_db != null ? ` · detect @ ${profile.margin_db}dB` : ""}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <select
                  disabled={busyId === profile.id || receivers.length === 0}
                  defaultValue=""
                  onChange={(event) => void handleApply(profile.id, event.target.value)}
                  className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-xs text-slate-300"
                >
                  <option value="" disabled>
                    Apply to...
                  </option>
                  {receivers.map((receiver) => (
                    <option key={receiver.id} value={receiver.id}>
                      {receiver.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={busyId === profile.id}
                  onClick={() => void handleDelete(profile.id)}
                  className="rounded-md px-2 py-1 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-40"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>

        {suggested.length > 0 && (
          <div className="border-t border-base-700 pt-3">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
              Suggested Presets
            </div>
            <ul className="space-y-2">
              {suggested.map((preset) => {
                const alreadySaved = savedFrequencies.has(preset.frequency_hz);
                return (
                  <li
                    key={preset.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-base-800 bg-base-900/40 px-3 py-2"
                  >
                    <div>
                      <div className="font-medium text-slate-300">{preset.name}</div>
                      <div className="text-xs text-slate-500" title={preset.description}>
                        {(preset.frequency_hz / 1e6).toFixed(4)} MHz
                        {preset.gain ? ` · gain ${preset.gain}` : ""}
                        {preset.decoder ? ` · ${preset.decoder.toUpperCase()} decoder` : ""}
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={busyId === preset.id || alreadySaved}
                      onClick={() => void handleAddSuggested(preset)}
                      className="rounded-md border border-base-600 px-2 py-1 text-xs text-slate-300 hover:bg-base-800 disabled:opacity-40"
                    >
                      {alreadySaved ? "Saved" : "Add"}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-2 border-t border-base-700 pt-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Name</label>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="2m Calling"
              className="w-32 rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100 placeholder:text-slate-500"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Frequency (MHz)</label>
            <input
              type="number"
              step="0.0001"
              value={frequencyMhz}
              onChange={(event) => setFrequencyMhz(event.target.value)}
              placeholder="146.5200"
              className="w-28 rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100 placeholder:text-slate-500"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500">Gain</label>
            <input
              value={gain}
              onChange={(event) => setGain(event.target.value)}
              placeholder="auto"
              className="w-20 rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100 placeholder:text-slate-500"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500" title="Auto-enables signal detection at this margin when applied">
              Detect margin (dB)
            </label>
            <input
              type="number"
              step="1"
              value={marginDb}
              onChange={(event) => setMarginDb(event.target.value)}
              placeholder="optional"
              className="w-24 rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100 placeholder:text-slate-500"
            />
          </div>
          <button
            type="submit"
            className="rounded-md bg-accent-500/20 px-3 py-1.5 text-accent-400 hover:bg-accent-500/30"
          >
            Save Profile
          </button>
        </form>
      </div>
    </Card>
  );
}
