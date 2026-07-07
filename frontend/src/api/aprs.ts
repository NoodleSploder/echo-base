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

export const listAprsStations = (receiverId?: string, minutes?: number) => {
  const params = new URLSearchParams();
  if (receiverId) params.set("receiver_id", receiverId);
  if (minutes) params.set("minutes", String(minutes));
  const query = params.toString();
  return api.get<AprsStation[]>(`/api/aprs/stations${query ? `?${query}` : ""}`);
};
