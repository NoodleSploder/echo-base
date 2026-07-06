import { api } from "../lib/apiClient";
import type { RecordingInfo } from "../types";

export const listRecordings = () => api.get<RecordingInfo[]>("/api/recordings");

export const startRecording = (receiverId: string, mode: string) =>
  api.post<RecordingInfo>(`/api/receivers/${encodeURIComponent(receiverId)}/recording/start`, { mode });
export const stopRecording = (receiverId: string) =>
  api.post<RecordingInfo>(`/api/receivers/${encodeURIComponent(receiverId)}/recording/stop`);

export const deleteRecording = (filename: string) =>
  api.delete<{ message: string }>(`/api/recordings/${encodeURIComponent(filename)}`);

export const recordingDownloadUrl = (filename: string) =>
  `/api/recordings/${encodeURIComponent(filename)}/download`;

export const startPlayback = (filename: string) =>
  api.post<{ playback_id: string }>(`/api/recordings/${encodeURIComponent(filename)}/playback/start`);
export const stopPlayback = (filename: string) =>
  api.post<{ message: string }>(`/api/recordings/${encodeURIComponent(filename)}/playback/stop`);

export const startTriggeredRecording = (receiverId: string, mode: string, durationSeconds: number) =>
  api.post<{ armed: boolean }>(
    `/api/receivers/${encodeURIComponent(receiverId)}/triggered-recording/start`,
    { mode, duration_seconds: durationSeconds },
  );
export const stopTriggeredRecording = (receiverId: string) =>
  api.post<{ armed: boolean }>(`/api/receivers/${encodeURIComponent(receiverId)}/triggered-recording/stop`);
