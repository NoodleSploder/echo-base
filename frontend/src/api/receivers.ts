import { api } from "../lib/apiClient";
import type { ReceiverDescriptor, ReceiverStatus } from "../types";

export const listReceivers = () => api.get<ReceiverDescriptor[]>("/api/receivers");
export const discoverReceivers = () => api.post<ReceiverDescriptor[]>("/api/receivers/discover");
export const getReceiver = (id: string) => api.get<ReceiverStatus>(`/api/receivers/${encodeURIComponent(id)}`);

export const startReceiver = (id: string) =>
  api.post<ReceiverStatus>(`/api/receivers/${encodeURIComponent(id)}/start`);
export const stopReceiver = (id: string) =>
  api.post<ReceiverStatus>(`/api/receivers/${encodeURIComponent(id)}/stop`);
export const tuneReceiver = (id: string, frequency: number) =>
  api.post<ReceiverStatus>(`/api/receivers/${encodeURIComponent(id)}/tune`, { frequency });

export const startAprsDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/aprs/start`);
export const stopAprsDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/aprs/stop`);

export const startSameDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/same/start`);
export const stopSameDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/same/stop`);

export const startSignalDetection = (id: string, marginDb: number) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/signal-detection/start`, {
    margin_db: marginDb,
  });
export const stopSignalDetection = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/signal-detection/stop`);
