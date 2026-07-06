import { api } from "../lib/apiClient";

export interface SatellitePass {
  aos_at: string;
  los_at: string;
  max_elevation_deg: number;
}

export interface PassPredictionRequest {
  tle_line1: string;
  tle_line2: string;
  latitude_deg: number;
  longitude_deg: number;
  elevation_m?: number;
  hours?: number;
  min_elevation_deg?: number;
}

export const predictSatellitePasses = (request: PassPredictionRequest) =>
  api.post<SatellitePass[]>("/api/satellites/passes", request);
