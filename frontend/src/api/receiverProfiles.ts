import { api } from "../lib/apiClient";
import type { ReceiverProfile, ReceiverProfileInput, ReceiverStatus } from "../types";

export const listReceiverProfiles = () => api.get<ReceiverProfile[]>("/api/receiver-profiles");
export const createReceiverProfile = (input: ReceiverProfileInput) =>
  api.post<ReceiverProfile>("/api/receiver-profiles", input);
export const updateReceiverProfile = (id: string, input: ReceiverProfileInput) =>
  api.put<ReceiverProfile>(`/api/receiver-profiles/${encodeURIComponent(id)}`, input);
export const deleteReceiverProfile = (id: string) =>
  api.delete<{ message: string }>(`/api/receiver-profiles/${encodeURIComponent(id)}`);
export const applyReceiverProfile = (profileId: string, receiverId: string) =>
  api.post<ReceiverStatus>(
    `/api/receiver-profiles/${encodeURIComponent(profileId)}/apply/${encodeURIComponent(receiverId)}`,
  );

export interface SuggestedReceiverProfile {
  id: string;
  name: string;
  frequency_hz: number;
  gain: string | null;
  decoder: string | null;
  description: string;
}

export const listSuggestedProfiles = () =>
  api.get<SuggestedReceiverProfile[]>("/api/receiver-profiles/suggested");
