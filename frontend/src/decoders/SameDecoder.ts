import { startSameDecoding, stopSameDecoding } from "../api/receivers";
import { registerDecoder } from "./DecoderRegistry";

registerDecoder({
  id: "same",
  name: "SAME",
  description:
    "Decoded NOAA Weather Radio SAME alerts appear in the Activity Feed, System Log, and Alerts widgets.",
  bands: [162_400_000, 162_425_000, 162_450_000, 162_475_000, 162_500_000, 162_525_000, 162_550_000].map(
    (hz) => ({
      hz,
      minHz: 162_400_000,
      maxHz: 162_550_000,
      label: `NOAA Weather Radio (${(hz / 1e6).toFixed(3)}MHz)`,
    }),
  ),
  healthKey: "same_enabled",
  start: startSameDecoding,
  stop: stopSameDecoding,
});
