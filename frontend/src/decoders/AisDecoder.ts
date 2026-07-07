import { startAisDecoding, stopAisDecoding } from "../api/receivers";
import { registerDecoder } from "./DecoderRegistry";

registerDecoder({
  id: "ais",
  name: "AIS",
  description:
    "Tune to a marine AIS channel (161.975MHz/162.025MHz) to decode anything real -- decoded vessels appear in the Activity Feed and System Log widgets.",
  bands: [{ minHz: 161_900_000, maxHz: 162_100_000, label: "Marine AIS (161.975/162.025MHz)" }],
  healthKey: "ais_enabled",
  start: startAisDecoding,
  stop: stopAisDecoding,
  // No AIS map layer yet -- position decoding is real (see the AIS
  // diary entry) but mapping work for it is on hold for now.
});
