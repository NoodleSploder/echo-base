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
export const setPpmCorrection = (id: string, ppm: number) =>
  api.post<ReceiverStatus>(`/api/receivers/${encodeURIComponent(id)}/ppm-correction`, { ppm });

export interface ScanStatus {
  active: boolean;
  frequencies?: number[];
  dwell_seconds?: number;
  current_index?: number;
  current_frequency_hz?: number;
}

export const startScan = (id: string, frequencies: number[], dwellSeconds: number) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/scan/start`, {
    frequencies,
    dwell_seconds: dwellSeconds,
  });
export const stopScan = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/scan/stop`);
export const getScanStatus = (id: string) =>
  api.get<ScanStatus>(`/api/receivers/${encodeURIComponent(id)}/scan/status`);

export const startAprsDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/aprs/start`);
export const stopAprsDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/aprs/stop`);

export const startSameDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/same/start`);
export const stopSameDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/same/stop`);

export const startAdsBDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/ads-b/start`);
export const stopAdsBDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/ads-b/stop`);

export const startAisDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/ais/start`);
export const stopAisDecoding = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/ais/stop`);

export const startSignalDetection = (id: string, marginDb: number) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/signal-detection/start`, {
    margin_db: marginDb,
  });
export const stopSignalDetection = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/signal-detection/stop`);

export interface OccupancySnapshot {
  frequencies_hz: number[];
  occupancy_percent: number[];
}

export const startOccupancy = (id: string, marginDb: number) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/occupancy/start`, {
    margin_db: marginDb,
  });
export const stopOccupancy = (id: string) =>
  api.post<{ message: string }>(`/api/receivers/${encodeURIComponent(id)}/occupancy/stop`);
export const getOccupancy = (id: string) =>
  api.get<OccupancySnapshot>(`/api/receivers/${encodeURIComponent(id)}/occupancy`);

export interface SignalHistoryRecord {
  frequency_hz: number | null;
  frequency_offset_hz: number;
  power_db: number;
  detected_at: string;
}

export const getSignalHistory = (id: string, minutes = 60) =>
  api.get<SignalHistoryRecord[]>(
    `/api/receivers/${encodeURIComponent(id)}/signal-history?minutes=${minutes}`,
  );

export interface CaptureHealth {
  active: boolean;
  alive?: boolean;
  read_count?: number;
  last_read_age_seconds?: number | null;
  spectrum_subscribers?: number;
  audio_subscribers?: number;
  iq_subscribers?: number;
  aprs_enabled?: boolean;
  same_enabled?: boolean;
  ads_b_enabled?: boolean;
  ais_enabled?: boolean;
  signal_detection_enabled?: boolean;
  occupancy_enabled?: boolean;
  triggered_recording_armed?: boolean;
}

export const getCaptureHealth = (id: string) =>
  api.get<CaptureHealth>(`/api/receivers/${encodeURIComponent(id)}/capture-health`);

export interface ReceiverInventoryRecord {
  receiver_id: string;
  name: string;
  driver: string;
  serial: string | null;
  first_seen_at: string;
  last_seen_at: string;
  attached: boolean;
}

export const getReceiverInventory = () =>
  api.get<ReceiverInventoryRecord[]>("/api/receivers/inventory");
