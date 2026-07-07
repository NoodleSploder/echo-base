// Sample/demo data for dashboard widgets that don't have a backend
// subsystem yet (Spectrum Intelligence, Digital Modes, Messaging,
// Recording, Alerting -- see ROADMAP.md). Widgets using this are
// visually tagged "Sample" in their panel header. Nothing here is
// persisted or represents real hardware/state.

export interface SampleReceiver {
  id: string;
  label: string;
  name: string;
  freqMhz: number;
  mode: string;
  colorClass: string;
  detail: Record<string, string>;
}

export const SAMPLE_RECEIVERS: SampleReceiver[] = [
  {
    id: "r1",
    label: "R1",
    name: "ADS-B",
    freqMhz: 1090.0,
    mode: "AM",
    colorClass: "bg-emerald-400",
    detail: { Aircraft: "256", "Msgs/s": "512.4", Signal: "P8" },
  },
  {
    id: "r2",
    label: "R2",
    name: "UAT",
    freqMhz: 978.0,
    mode: "AM",
    colorClass: "bg-sky-400",
    detail: { Aircraft: "45", "Msgs/s": "128.7", Signal: "P6" },
  },
  {
    id: "r3",
    label: "R3",
    name: "NOAA WX",
    freqMhz: 137.1,
    mode: "FM-N",
    colorClass: "bg-emerald-400",
    detail: { Sat: "NOAA 19", Elev: "45°" },
  },
  {
    id: "r4",
    label: "R4",
    name: "AIRBAND",
    freqMhz: 118.0,
    mode: "AM",
    colorClass: "bg-violet-400",
    detail: { Station: "KJFK Tower", CTAF: "118.000" },
  },
  {
    id: "r5",
    label: "R5",
    name: "VHF PUBLIC SAFETY",
    freqMhz: 155.55,
    mode: "NFM",
    colorClass: "bg-amber-400",
    detail: { Agency: "County Sheriff", Channel: "Dispatch" },
  },
  {
    id: "r6",
    label: "R6",
    name: "UHF PUBLIC SAFETY",
    freqMhz: 453.225,
    mode: "NFM",
    colorClass: "bg-sky-400",
    detail: { Agency: "City Police", Channel: "South Tac" },
  },
  {
    id: "r7",
    label: "R7",
    name: "AMATEUR RADIO",
    freqMhz: 144.2,
    mode: "FM",
    colorClass: "bg-emerald-400",
    detail: { Call: "K7ABC", Grid: "JN37wd" },
  },
  {
    id: "r8",
    label: "R8",
    name: "WIDEBAND SEARCH",
    freqMhz: 849.125,
    mode: "AM",
    colorClass: "bg-orange-400",
    detail: { Peak: "-45.2 dB", SNR: "18.7 dB" },
  },
];

export interface SampleAlert {
  id: string;
  severity: "info" | "warning" | "critical";
  source: string;
  message: string;
  time: string;
}

export const SAMPLE_ALERTS: SampleAlert[] = [
  { id: "a1", severity: "warning", source: "R5 P25", message: "Activity detected", time: "10:42" },
  { id: "a2", severity: "info", source: "R1 ADS-B", message: "Rate high (1000 msgs/s)", time: "10:40" },
  { id: "a3", severity: "info", source: "R8", message: "New signal at 849.125 MHz", time: "10:38" },
];

export const MESSAGING_TABS = ["APRS", "WINLINK", "JS8CALL", "VARA HF", "FLDIGI"];

export interface SampleAprsMessage {
  from: string;
  time: string;
  freq: string;
  text: string;
}

export const SAMPLE_APRS_MESSAGES: SampleAprsMessage[] = [
  { from: "NOCALL-7", time: "10:42:18", freq: "144.390", text: "K7ABC-10>APRS: Hello from Denver!" },
  { from: "K7ABC-10", time: "10:42:15", freq: "144.390", text: "NOCALL-7: Roger that!" },
  { from: "WIDE1-1", time: "10:41:59", freq: "144.390", text: "Bulletin: Field Day next weekend" },
  { from: "K7GPS-3", time: "10:41:32", freq: "144.390", text: "@123456h4450.12N/09312.45W-Test" },
  { from: "NOCALL-7", time: "10:41:10", freq: "144.390", text: "qAR NOCALL-7 Denver, CO" },
  { from: "K7ABC-10", time: "10:40:55", freq: "144.390", text: "qAR K7ABC-10 Boulder, CO" },
];

export interface SampleRecording {
  id: string;
  recorder: string;
  freq: string;
  start: string;
  duration: string;
  size: string;
}

export const SAMPLE_RECORDINGS: SampleRecording[] = [
  { id: "rec1", recorder: "R1 - ADS-B", freq: "1090.000 MHz", start: "2026-07-05 10:30", duration: "00:12:37", size: "1.2 GB" },
  { id: "rec2", recorder: "R4 - AIRBAND", freq: "118.000 MHz", start: "2026-07-05 10:25", duration: "00:18:42", size: "892 MB" },
  { id: "rec3", recorder: "R5 - VHF PUBLIC SAFETY", freq: "155.550 MHz", start: "2026-07-05 10:15", duration: "00:45:18", size: "2.1 GB" },
  { id: "rec4", recorder: "R8 - WIDEBAND SEARCH", freq: "849.125 MHz", start: "2026-07-05 09:50", duration: "01:22:33", size: "4.8 GB" },
];
