import { Panel } from "../common/Panel";
import { SAMPLE_FT8_DECODES } from "../../lib/sampleData";

export function DigitalDecodesWidget() {
  return (
    <Panel title="Digital Decodes -- FT8 (14.074 MHz)" sample bodyClassName="p-2">
      <table className="w-full text-left text-xs">
        <thead className="text-slate-500">
          <tr>
            <th className="pb-1 font-medium">UTC</th>
            <th className="pb-1 font-medium">dB</th>
            <th className="pb-1 font-medium">DT</th>
            <th className="pb-1 font-medium">Callsign</th>
            <th className="pb-1 font-medium">Grid</th>
            <th className="pb-1 font-medium">Message</th>
          </tr>
        </thead>
        <tbody>
          {SAMPLE_FT8_DECODES.map((decode, index) => (
            <tr key={index} className="border-t border-base-800">
              <td className="py-1 text-slate-400">{decode.utc}</td>
              <td className="py-1 text-slate-300">{decode.db}</td>
              <td className="py-1 text-slate-300">{decode.dt}</td>
              <td className="py-1 font-medium text-accent-400">{decode.callsign}</td>
              <td className="py-1 text-slate-300">{decode.grid}</td>
              <td className="py-1 text-slate-300">{decode.msg}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
