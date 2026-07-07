import { startAisDecoding, stopAisDecoding } from "../api/receivers";
import { AisVesselsPanel } from "../components/receivers/AisVesselsPanel";
import { registerDecoder } from "./DecoderRegistry";

registerDecoder({
  id: "ais",
  name: "AIS",
  description:
    "Tune to a marine AIS channel (161.975MHz/162.025MHz) to decode anything real -- decoded vessels appear in the Activity Feed and System Log widgets.",
  bands: [
    { hz: 161_975_000, minHz: 161_900_000, maxHz: 162_000_000, label: "AIS Channel A (161.975MHz)" },
    { hz: 162_025_000, minHz: 162_000_000, maxHz: 162_100_000, label: "AIS Channel B (162.025MHz)" },
  ],
  healthKey: "ais_enabled",
  start: startAisDecoding,
  stop: stopAisDecoding,
  Panel: AisVesselsPanel,
  // No AIS map layer yet -- position decoding is real (see the AIS
  // diary entry) but mapping work for it is on hold for now.
});
