import { startSstvDecoding, stopSstvDecoding } from "../api/receivers";
import { registerDecoder } from "./DecoderRegistry";
import { SstvPanel } from "./SstvPanel";

registerDecoder({
  id: "sstv",
  name: "SSTV",
  description:
    "Slow-Scan TV: tune to a real SSTV frequency to watch a picture decode live, line by line.",
  bands: [
    { hz: 145_800_000, minHz: 145_790_000, maxHz: 145_810_000, label: "2m FM (145.800MHz, ISS SSTV events)" },
    { hz: 14_230_000, minHz: 14_225_000, maxHz: 14_235_000, label: "20m SSTV (14.230MHz)" },
    { hz: 7_171_000, minHz: 7_166_000, maxHz: 7_176_000, label: "40m SSTV (7.171MHz)" },
    { hz: 3_845_000, minHz: 3_840_000, maxHz: 3_850_000, label: "80m SSTV (3.845MHz)" },
  ],
  healthKey: "sstv_enabled",
  start: startSstvDecoding,
  stop: stopSstvDecoding,
  Panel: SstvPanel,
});
