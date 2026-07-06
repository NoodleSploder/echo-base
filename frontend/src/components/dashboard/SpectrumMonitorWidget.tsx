import { useReceiverPicker } from "../../hooks/useReceiverPicker";
import { useSpectrumStream } from "../../hooks/useWebSocket";
import { Panel } from "../common/Panel";
import { SpectrumCanvas } from "../common/SpectrumCanvas";

// Real data when a receiver supports IQ streaming (currently rtl_sdr):
// the FFT is computed server-side and streamed as binary frames over
// /ws/spectrum/{receiver_id} (see SpectrumService). Falls back to the
// decorative sample animation otherwise.
export function SpectrumMonitorWidget() {
  const { receivers, selectedId, setSelectedId } = useReceiverPicker();
  const { frame, connected } = useSpectrumStream(selectedId);

  return (
    <Panel
      title="Spectrum Monitor"
      sample={!connected}
      bodyClassName="p-2"
      actions={
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {receivers.length > 1 && (
            <select
              value={selectedId ?? ""}
              onChange={(event) => setSelectedId(event.target.value)}
              className="rounded border border-base-600 bg-base-800 px-1 py-0.5 text-slate-300"
            >
              {receivers.map((receiver) => (
                <option key={receiver.id} value={receiver.id}>
                  {receiver.name}
                </option>
              ))}
            </select>
          )}
          <span>{connected ? "FFT 1024" : "FFT 16384 · RBW 7.6 kHz"}</span>
        </div>
      }
    >
      <SpectrumCanvas height={160} liveFrame={frame} />
    </Panel>
  );
}
