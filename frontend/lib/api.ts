const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access");
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access: string };
  localStorage.setItem("access", data.access);
  return data.access;
}

/** Authenticated fetch with automatic token refresh on 401. */
export async function authFetch(path: string, init: RequestInit = {}, retried = false): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (res.status === 401 && !retried) {
    if (!refreshInFlight) {
      refreshInFlight = refreshAccessToken().finally(() => {
        refreshInFlight = null;
      });
    }
    const newAccess = await refreshInFlight;
    if (newAccess) return authFetch(path, init, true);
    clearTokens();
  }
  return res;
}

export async function apiJson<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string>),
  };
  if (init.json !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const res = await authFetch(path, {
    ...init,
    headers,
    body: init.json !== undefined ? JSON.stringify(init.json) : init.body,
  });
  if (!res.ok) {
    let detail: string = res.statusText;
    try {
      const err = (await res.json()) as { detail?: unknown };
      if (typeof err.detail === "string") detail = err.detail;
      else if (Array.isArray(err.detail)) detail = JSON.stringify(err.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function uploadDocument(projectId: string, file: File): Promise<unknown> {
  const form = new FormData();
  form.append("file", file);
  const res = await authFetch(`/api/projects/${projectId}/documents/`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.json();
}

export async function retryDocument(projectId: string, documentId: string): Promise<unknown> {
  return apiJson(`/api/projects/${projectId}/documents/${documentId}/retry/`, { method: "POST" });
}

export type Project = { id: string; name: string; created_at: string };

export async function updateProject(projectId: string, name: string): Promise<Project> {
  return apiJson<Project>(`/api/projects/${projectId}/`, {
    method: "PATCH",
    json: { name },
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await authFetch(`/api/projects/${projectId}/`, { method: "DELETE" });
  if (!res.ok) {
    let detail: string = res.statusText;
    try {
      const err = (await res.json()) as { detail?: unknown };
      if (typeof err.detail === "string") detail = err.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
}

export type ChunkDetail = {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number | null;
  chunk_index: number;
  content: string;
  token_count: number;
};

export async function fetchChunkDetail(projectId: string, chunkId: string): Promise<ChunkDetail> {
  return apiJson<ChunkDetail>(`/api/projects/${projectId}/chunks/${chunkId}/`);
}
