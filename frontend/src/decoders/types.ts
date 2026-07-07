import type { ComponentType } from "react";
import type { CaptureHealth } from "../api/receivers";

export interface FrequencyBand {
  /** The actual frequency to tune a receiver to when this band is
   * picked from a decoder panel's "tune to" dropdown -- distinct from
   * `minHz`/`maxHz` below, which describe a *range* still considered
   * "in band" (e.g. FT8's ~3.5kHz USB passband above its dial
   * frequency), not necessarily centered on `hz`. */
  hz: number;
  minHz: number;
  maxHz: number;
  label: string;
}

export interface DecoderPanelProps {
  receiverId: string;
}

export interface DecoderDefinition {
  id: string;
  name: string;
  description: string;
  /** Frequency ranges this decoder is meant for -- used to decide
   * whether the receiver's current tuning is "in band" for it. A
   * decoder can list several (e.g. FT8's many HF dial frequencies). */
  bands: FrequencyBand[];
  /** Which field of `GET .../capture-health` reflects this decoder's
   * enabled state. */
  healthKey: keyof CaptureHealth;
  start: (receiverId: string) => Promise<unknown>;
  stop: (receiverId: string) => Promise<unknown>;
  /** The `geo/layers` MapLayer id this decoder's real data feeds, if
   * any -- a real "relates to" link between a decoder and the map
   * layer it populates, so the UI can say so instead of the two being
   * silently unrelated. */
  feedsMapLayer?: string;
  /** An optional live panel rendered inline while this decoder is
   * enabled (e.g. SSTV's progressively-decoding image). Mounted only
   * while enabled, so it can manage its own polling lifecycle without
   * an explicit "enabled" prop. */
  Panel?: ComponentType<DecoderPanelProps>;
}
