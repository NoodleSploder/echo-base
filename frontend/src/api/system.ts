import { api } from "../lib/apiClient";
import type { HealthStatus, SystemInfo } from "../types";

export const getHealth = () => api.get<HealthStatus>("/api/system/health");
export const getSystemInfo = () => api.get<SystemInfo>("/api/system");
