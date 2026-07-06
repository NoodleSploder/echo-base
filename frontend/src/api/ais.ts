import { api } from "../lib/apiClient";

export interface AisVessel {
  receiver_id: string;
  mmsi: number;
  last_message_type: number;
  message_count: number;
  first_seen_at: string;
  last_seen_at: string;
}

export const listAisVessels = (minutes?: number) =>
  api.get<AisVessel[]>(`/api/ais/vessels${minutes ? `?minutes=${minutes}` : ""}`);
