export class ApiError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

interface Envelope<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  const body = (await response.json().catch(() => null)) as Envelope<T> | null;

  if (!response.ok || !body || body.success === false) {
    const error = body?.error;
    throw new ApiError(error?.code ?? "UNKNOWN_ERROR", error?.message ?? response.statusText, response.status);
  }

  return body.data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, json?: unknown) =>
    request<T>(path, { method: "POST", body: json !== undefined ? JSON.stringify(json) : undefined }),
  put: <T>(path: string, json?: unknown) =>
    request<T>(path, { method: "PUT", body: json !== undefined ? JSON.stringify(json) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
