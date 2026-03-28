import axios from "axios";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { "Content-Type": "application/json" },
});

function getStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  const candidate = (globalThis as { localStorage?: Partial<Storage> }).localStorage;
  if (!candidate) return null;
  if (typeof candidate.getItem !== "function") return null;
  if (typeof candidate.setItem !== "function") return null;
  if (typeof candidate.removeItem !== "function") return null;
  return candidate as Storage;
}

api.interceptors.request.use((config) => {
  const storage = getStorage();
  if (storage) {
    const token = storage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export function setTokens(access: string, refresh: string) {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem("access_token", access);
  storage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  const storage = getStorage();
  if (!storage) return;
  storage.removeItem("access_token");
  storage.removeItem("refresh_token");
}

export function getAccessToken(): string | null {
  const storage = getStorage();
  if (!storage) return null;
  return storage.getItem("access_token");
}

export async function refreshAccessToken(): Promise<string | null> {
  const storage = getStorage();
  if (!storage) return null;
  const refresh = storage.getItem("refresh_token");
  if (!refresh) return null;
  const { data } = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
    refresh,
  });
  storage.setItem("access_token", data.access);
  return data.access as string;
}
