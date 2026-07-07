import { api } from "../lib/apiClient";

export interface Ft8Station {
  receiver_id: string;
  callsign: string;
  grid: string | null;
  latitude: number | null;
  longitude: number | null;
  last_message: string;
  frequency_offset_hz: number;
  message_count: number;
  first_heard_at: string;
  last_heard_at: string;
}

export const listFt8Stations = (receiverId?: string, minutes?: number) => {
  const params = new URLSearchParams();
  if (receiverId) params.set("receiver_id", receiverId);
  if (minutes) params.set("minutes", String(minutes));
  const query = params.toString();
  return api.get<Ft8Station[]>(`/api/ft8/stations${query ? `?${query}` : ""}`);
};
