import { api } from "../lib/apiClient";

export interface AdsbAircraft {
  receiver_id: string;
  icao: string;
  last_type_code: number;
  message_count: number;
  first_seen_at: string;
  last_seen_at: string;
  latitude: number | null;
  longitude: number | null;
}

export const listAdsbAircraft = (minutes?: number) =>
  api.get<AdsbAircraft[]>(`/api/adsb/aircraft${minutes ? `?minutes=${minutes}` : ""}`);
