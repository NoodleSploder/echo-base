import { Panel } from "../common/Panel";
import { SAMPLE_RECORDINGS } from "../../lib/sampleData";

export function RecordingsWidget() {
  return (
    <Panel title="Recordings" sample bodyClassName="p-2">
      <table className="w-full text-left text-xs">
        <thead className="text-slate-500">
          <tr>
            <th className="pb-1 font-medium">Recorder</th>
            <th className="pb-1 font-medium">Freq</th>
            <th className="pb-1 font-medium">Start</th>
            <th className="pb-1 font-medium">Duration</th>
            <th className="pb-1 font-medium">Size</th>
          </tr>
        </thead>
        <tbody>
          {SAMPLE_RECORDINGS.map((recording) => (
            <tr key={recording.id} className="border-t border-base-800">
              <td className="py-1 text-slate-200">{recording.recorder}</td>
              <td className="py-1 text-slate-400">{recording.freq}</td>
              <td className="py-1 text-slate-400">{recording.start}</td>
              <td className="py-1 text-slate-400">{recording.duration}</td>
              <td className="py-1 text-slate-400">{recording.size}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" disabled className="mt-2 w-full cursor-not-allowed rounded-md border border-base-600 py-1.5 text-xs text-slate-500">
        View All Recordings
      </button>
    </Panel>
  );
}
