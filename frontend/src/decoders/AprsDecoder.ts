import { startAprsDecoding, stopAprsDecoding } from "../api/receivers";
import { AprsStationsPanel } from "./AprsStationsPanel";
import { registerDecoder } from "./DecoderRegistry";

registerDecoder({
  id: "aprs",
  name: "APRS",
  description:
    "Decoded APRS packets appear in the Activity Feed, System Log, and Messaging Center widgets.",
  bands: [
    { hz: 144_390_000, minHz: 144_000_000, maxHz: 148_000_000, label: "APRS North America (144.390MHz)" },
    { hz: 144_800_000, minHz: 144_000_000, maxHz: 148_000_000, label: "APRS Europe (144.800MHz)" },
  ],
  healthKey: "aprs_enabled",
  start: startAprsDecoding,
  stop: stopAprsDecoding,
  feedsMapLayer: "aprs-stations",
  Panel: AprsStationsPanel,
});
