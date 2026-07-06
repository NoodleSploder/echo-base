import { api } from "../lib/apiClient";
import type { PluginSummary } from "../types";

export const listPlugins = () => api.get<PluginSummary[]>("/api/plugins");
