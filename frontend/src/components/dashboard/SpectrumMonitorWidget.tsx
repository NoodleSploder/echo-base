import { useFirstReceiver } from "../../hooks/useFirstReceiver";
import { useSpectrumStream } from "../../hooks/useWebSocket";
import { Panel } from "../common/Panel";
import { SpectrumCanvas } from "../common/SpectrumCanvas";

// Real data when a receiver supports IQ streaming (currently rtl_sdr):
// the FFT is computed server-side and streamed as binary frames over
// /ws/spectrum/{receiver_id} (see SpectrumService). Falls back to the
// decorative sample animation otherwise.
export function SpectrumMonitorWidget() {
  const receiverId = useFirstReceiver();
  const { frame, connected } = useSpectrumStream(receiverId);

  return (
    <Panel
      title="Spectrum Monitor"
      sample={!connected}
      bodyClassName="p-2"
      actions={
        <span className="text-xs text-slate-500">
          {connected ? `FFT 1024 · ${receiverId}` : "FFT 16384 · RBW 7.6 kHz"}
        </span>
      }
    >
      <SpectrumCanvas height={160} liveFrame={frame} />
    </Panel>
  );
}
