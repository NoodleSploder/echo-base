import { startFt8Decoding, stopFt8Decoding } from "../api/receivers";
import { registerDecoder } from "./DecoderRegistry";

// Standard FT8 dial (USB suppressed-carrier) frequencies -- the actual
// tones live in the ~0-3kHz passband above each of these, so each band
// extends a bit above the dial frequency (and a little below, for
// tuning slop) rather than being a single point.
const FT8_DIAL_FREQUENCIES_HZ = [
  1_840_000, 3_573_000, 5_357_000, 7_074_000, 10_136_000, 14_074_000, 18_100_000, 21_074_000, 24_915_000,
  28_074_000, 50_313_000,
];

registerDecoder({
  id: "ft8",
  name: "FT8",
  description:
    "Tune to a real FT8 dial frequency (USB) -- needs HF coverage, not just a plain RTL-SDR's native VHF/UHF range. Decodes appear on the map and in the Activity Feed; a whole ~15s slot has to complete before anything shows up.",
  bands: FT8_DIAL_FREQUENCIES_HZ.map((dialHz) => ({
    minHz: dialHz - 1000,
    maxHz: dialHz + 3500,
    label: `${(dialHz / 1e6).toFixed(3)}MHz FT8`,
  })),
  healthKey: "ft8_enabled",
  start: startFt8Decoding,
  stop: stopFt8Decoding,
  feedsMapLayer: "ft8-stations",
});
