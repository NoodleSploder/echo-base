import { startSameDecoding, stopSameDecoding } from "../api/receivers";
import { registerDecoder } from "./DecoderRegistry";

registerDecoder({
  id: "same",
  name: "SAME",
  description:
    "Decoded NOAA Weather Radio SAME alerts appear in the Activity Feed, System Log, and Alerts widgets.",
  bands: [
    { minHz: 162_400_000, maxHz: 162_550_000, label: "NOAA Weather Radio (7 channels, 162.400-162.550MHz)" },
  ],
  healthKey: "same_enabled",
  start: startSameDecoding,
  stop: stopSameDecoding,
});
