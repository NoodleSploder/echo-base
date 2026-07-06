import { api } from "../lib/apiClient";

export interface DashboardLayoutData {
  layout: Record<string, unknown> | null;
}

export const getDashboardLayout = () => api.get<DashboardLayoutData>("/api/dashboard/layout");
export const saveDashboardLayout = (layout: Record<string, unknown>) =>
  api.put<{ message: string }>("/api/dashboard/layout", { layout });
