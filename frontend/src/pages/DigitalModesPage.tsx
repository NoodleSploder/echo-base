import { getRegisteredDecoders } from "../decoders/DecoderRegistry";
import { DecoderPanel } from "../decoders/DecoderPanel";
import "../decoders"; // side-effect import: every decoder module registers itself

// Each decoder is an independent, self-contained panel pointed at
// whichever receiver you choose (see decoders/DecoderPanel.tsx) --
// not a feature bolted onto a specific receiver's own card. Switching
// between several of these, each listening with its own receiver/
// config, is the normal way to use this page.
export function DigitalModesPage() {
  const decoders = getRegisteredDecoders();

  return (
    <div>
      <p className="mb-3 text-xs text-slate-500">
        Each panel below is independent -- point it at any receiver, configure it, and switch between
        panels freely. A decoder's toggle stays visible even when the receiver is tuned outside its
        typical band, just de-emphasized.
      </p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {decoders.map((decoder) => (
          <DecoderPanel key={decoder.id} decoder={decoder} />
        ))}
      </div>
    </div>
  );
}
