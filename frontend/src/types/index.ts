export type UserRole = "administrator" | "operator" | "observer" | "guest";

export interface CurrentUser {
  id: string;
  username: string;
  role: UserRole;
  disabled: boolean;
}

export interface ReceiverDescriptor {
  id: string;
  name: string;
  driver: string;
  serial: string | null;
  capabilities: Record<string, unknown>;
}

export type ReceiverState = "idle" | "streaming" | "error" | "disconnected";

export interface ReceiverStatus {
  id: string;
  state: ReceiverState;
  frequency_hz: number | null;
  sample_rate_hz: number | null;
  bandwidth_hz: number | null;
  gain: string | number | null;
  detail: string | null;
}

export interface PluginSummary {
  id: string;
  name: string;
  version: string;
  plugin_type: string;
  enabled: boolean;
  status: Record<string, unknown>;
}

export interface SystemInfo {
  name: string;
  version: string;
  environment: string;
  hostname: string;
  platform: string;
  uptime_seconds: number;
}

export interface HealthStatus {
  status: string;
  database: string;
  plugins_loaded: number;
}

export interface EchoBaseEvent {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  data: Record<string, unknown>;
}
