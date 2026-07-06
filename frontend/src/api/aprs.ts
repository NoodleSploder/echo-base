import { api } from "../lib/apiClient";

export interface AprsStation {
  receiver_id: string;
  callsign: string;
  latitude: number;
  longitude: number;
  symbol: string | null;
  last_info: string;
  first_heard_at: string;
  last_heard_at: string;
}

export const listAprsStations = (minutes?: number) =>
  api.get<AprsStation[]>(`/api/aprs/stations${minutes ? `?minutes=${minutes}` : ""}`);
