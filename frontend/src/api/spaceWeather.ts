import { api } from "../lib/apiClient";

export interface KpReading {
  time_tag: string;
  Kp: number;
  a_running: number;
  station_count: number;
}

export interface KpIndexResponse {
  readings: KpReading[];
  cached_at: string;
}

export const getKpIndex = () => api.get<KpIndexResponse>("/api/space-weather/kp-index");

export interface AuroraMeta {
  observation_time: string;
  forecast_time: string;
  cached_at: string;
}

export const getAuroraMeta = () => api.get<AuroraMeta>("/api/space-weather/aurora/meta");

// Not fetched through the shared `api` client -- this is handed
// straight to Leaflet's L.imageOverlay as a src URL, the same way a
// plain <img> tag would use it. The session cookie rides along
// automatically since it's a same-origin GET.
export const AURORA_PNG_PATH = "/api/space-weather/aurora.png";
