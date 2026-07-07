import type { DecoderDefinition } from "./types";

const registry: DecoderDefinition[] = [];

export function registerDecoder(definition: DecoderDefinition): void {
  registry.push(definition);
}

export function getRegisteredDecoders(): DecoderDefinition[] {
  return registry;
}

export function isInBand(definition: DecoderDefinition, frequencyHz: number | null): boolean {
  if (frequencyHz === null) return false;
  return definition.bands.some((band) => frequencyHz >= band.minHz && frequencyHz <= band.maxHz);
}
