import { startFt8Decoding, stopFt8Decoding } from "../api/receivers";
import { registerDecoder } from "./DecoderRegistry";
import { Ft8StationsPanel } from "./Ft8StationsPanel";

// Standard FT8 dial (USB suppressed-carrier) frequencies per band --
// the actual tones live in the ~0-3kHz passband above each of these,
// so each band's "in range" window extends a bit above the dial
// frequency (and a little below, for tuning slop) rather than being a
// single point.
const FT8_BAND_PLAN: { label: string; hz: number }[] = [
  { label: "160m", hz: 1_840_000 },
  { label: "80m", hz: 3_573_000 },
  { label: "60m", hz: 5_357_000 },
  { label: "40m", hz: 7_074_000 },
  { label: "30m", hz: 10_136_000 },
  { label: "20m", hz: 14_074_000 },
  { label: "17m", hz: 18_100_000 },
  { label: "15m", hz: 21_074_000 },
  { label: "12m", hz: 24_915_000 },
  { label: "10m", hz: 28_074_000 },
  { label: "6m", hz: 50_313_000 },
  { label: "2m", hz: 144_174_000 },
  { label: "70cm", hz: 432_174_000 },
];

registerDecoder({
  id: "ft8",
  name: "FT8",
  description:
    "Tune to a real FT8 dial frequency (USB) -- needs HF coverage for most bands, not just a plain RTL-SDR's native VHF/UHF range (2m/70cm are reachable directly). Decodes appear on the map and in the Activity Feed; a whole ~15s slot has to complete before anything shows up.",
  bands: FT8_BAND_PLAN.map(({ label, hz }) => ({
    hz,
    minHz: hz - 1000,
    maxHz: hz + 3500,
    label: `${label} (${(hz / 1e6).toFixed(3)}MHz)`,
  })),
  healthKey: "ft8_enabled",
  start: startFt8Decoding,
  stop: stopFt8Decoding,
  feedsMapLayer: "ft8-stations",
  Panel: Ft8StationsPanel,
});
