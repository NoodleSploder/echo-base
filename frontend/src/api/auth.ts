import { api } from "../lib/apiClient";
import type { CurrentUser } from "../types";

export interface LoginResult {
  username: string;
  role: string;
  must_change_password: boolean;
}

export const login = (username: string, password: string) =>
  api.post<LoginResult>("/api/auth/login", { username, password });

export const logout = () => api.post<{ message: string }>("/api/auth/logout");

export const me = () => api.get<CurrentUser>("/api/auth/me");
