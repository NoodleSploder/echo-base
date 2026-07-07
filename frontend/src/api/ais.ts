import { api } from "../lib/apiClient";

export interface AisVessel {
  receiver_id: string;
  mmsi: number;
  last_message_type: number;
  message_count: number;
  first_seen_at: string;
  last_seen_at: string;
  latitude: number | null;
  longitude: number | null;
}

export const listAisVessels = (receiverId?: string, minutes?: number) => {
  const params = new URLSearchParams();
  if (receiverId) params.set("receiver_id", receiverId);
  if (minutes) params.set("minutes", String(minutes));
  const query = params.toString();
  return api.get<AisVessel[]>(`/api/ais/vessels${query ? `?${query}` : ""}`);
};
