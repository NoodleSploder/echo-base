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

export const listAdsbAircraft = (receiverId?: string, minutes?: number) => {
  const params = new URLSearchParams();
  if (receiverId) params.set("receiver_id", receiverId);
  if (minutes) params.set("minutes", String(minutes));
  const query = params.toString();
  return api.get<AdsbAircraft[]>(`/api/adsb/aircraft${query ? `?${query}` : ""}`);
};
