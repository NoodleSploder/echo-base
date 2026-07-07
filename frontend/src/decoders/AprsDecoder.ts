import { startAprsDecoding, stopAprsDecoding } from "../api/receivers";
import { registerDecoder } from "./DecoderRegistry";

registerDecoder({
  id: "aprs",
  name: "APRS",
  description:
    "Decoded APRS packets appear in the Activity Feed, System Log, and Messaging Center widgets.",
  bands: [
    { minHz: 144_000_000, maxHz: 148_000_000, label: "2m APRS/packet (144.390MHz in North America)" },
  ],
  healthKey: "aprs_enabled",
  start: startAprsDecoding,
  stop: stopAprsDecoding,
  feedsMapLayer: "aprs-stations",
});
