import { startAdsBDecoding, stopAdsBDecoding } from "../api/receivers";
import { AdsbAircraftPanel } from "../components/receivers/AdsbAircraftPanel";
import { registerDecoder } from "./DecoderRegistry";

registerDecoder({
  id: "ads-b",
  name: "ADS-B",
  description:
    "Needs a wideband capture (tune to 1090MHz, sample rate >=2MS/s) to decode anything real -- decoded aircraft appear on the map and in the Activity Feed.",
  bands: [
    { hz: 1_090_000_000, minHz: 1_088_000_000, maxHz: 1_092_000_000, label: "1090MHz Mode S/ADS-B" },
  ],
  healthKey: "ads_b_enabled",
  start: startAdsBDecoding,
  stop: stopAdsBDecoding,
  feedsMapLayer: "adsb-aircraft",
  Panel: AdsbAircraftPanel,
});
