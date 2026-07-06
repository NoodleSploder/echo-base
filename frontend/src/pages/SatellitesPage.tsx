import { useState, type FormEvent } from "react";
import { predictSatellitePasses, type SatellitePass } from "../api/satellites";
import { Card } from "../components/common/Card";

// TLEs go stale within 1-2 weeks -- this deliberately doesn't bundle
// or fetch one (see satellite_passes.py's docstring); paste a current
// one from a source like Celestrak (celestrak.org).
export function SatellitesPage() {
  const [tleLine1, setTleLine1] = useState("");
  const [tleLine2, setTleLine2] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [elevation, setElevation] = useState("0");
  const [minElevation, setMinElevation] = useState("10");
  const [hours, setHours] = useState("24");
  const [passes, setPasses] = useState<SatellitePass[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await predictSatellitePasses({
        tle_line1: tleLine1.trim(),
        tle_line2: tleLine2.trim(),
        latitude_deg: Number(latitude),
        longitude_deg: Number(longitude),
        elevation_m: Number(elevation) || 0,
        hours: Number(hours) || 24,
        min_elevation_deg: Number(minElevation) || 10,
      });
      setPasses(result);
    } catch {
      setError("Could not predict passes -- check the TLE lines and coordinates.");
      setPasses(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-slate-100">Satellite Pass Prediction</h1>

      <Card title="Predict Passes">
        <form onSubmit={(event) => void handleSubmit(event)} className="space-y-3 text-sm">
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <input
              value={tleLine1}
              onChange={(event) => setTleLine1(event.target.value)}
              placeholder="TLE line 1"
              className="rounded-md border border-base-600 bg-base-800 px-2 py-1 font-mono text-xs text-slate-100 placeholder:text-slate-500"
            />
            <input
              value={tleLine2}
              onChange={(event) => setTleLine2(event.target.value)}
              placeholder="TLE line 2"
              className="rounded-md border border-base-600 bg-base-800 px-2 py-1 font-mono text-xs text-slate-100 placeholder:text-slate-500"
            />
          </div>
          <p className="text-xs text-slate-500">
            Paste a current TLE for your satellite (e.g. from celestrak.org) -- orbital elements go
            stale within 1-2 weeks, so none is bundled here.
          </p>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500">Latitude</label>
              <input
                type="number"
                value={latitude}
                onChange={(event) => setLatitude(event.target.value)}
                className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500">Longitude</label>
              <input
                type="number"
                value={longitude}
                onChange={(event) => setLongitude(event.target.value)}
                className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500">Elevation (m)</label>
              <input
                type="number"
                value={elevation}
                onChange={(event) => setElevation(event.target.value)}
                className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500">Min elevation (deg)</label>
              <input
                type="number"
                value={minElevation}
                onChange={(event) => setMinElevation(event.target.value)}
                className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500">Window (hours)</label>
              <input
                type="number"
                value={hours}
                onChange={(event) => setHours(event.target.value)}
                className="rounded-md border border-base-600 bg-base-800 px-2 py-1 text-slate-100"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={busy || !tleLine1 || !tleLine2 || !latitude || !longitude}
            className="rounded-md bg-accent-500/20 px-3 py-1.5 text-accent-400 hover:bg-accent-500/30 disabled:opacity-50"
          >
            {busy ? "Predicting..." : "Predict Passes"}
          </button>
          {error && <p className="text-xs text-red-400">{error}</p>}
        </form>
      </Card>

      {passes && (
        <Card title={`${passes.length} Pass(es) Found`}>
          {passes.length === 0 ? (
            <p className="text-sm text-slate-500">No passes above the minimum elevation in this window.</p>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="text-slate-500">
                <tr>
                  <th className="pb-1 font-medium">AOS</th>
                  <th className="pb-1 font-medium">LOS</th>
                  <th className="pb-1 font-medium">Max Elevation</th>
                </tr>
              </thead>
              <tbody>
                {passes.map((pass, index) => (
                  <tr key={index} className="border-t border-base-800">
                    <td className="py-1 text-slate-200">{new Date(pass.aos_at).toLocaleString()}</td>
                    <td className="py-1 text-slate-200">{new Date(pass.los_at).toLocaleString()}</td>
                    <td className="py-1 text-slate-400">{pass.max_elevation_deg}&deg;</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}
    </div>
  );
}
