import { User, Trip, TripPoint, FuelStats } from "./types";

declare global {
  interface ImportMetaEnv {
    VITE_API_BASE?: string;
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

// Allow overriding API base for mobile access: set VITE_API_BASE to e.g. http://<PC_IP>:4000 when accessed from phone
const API_BASE = (import.meta as ImportMeta).env.VITE_API_BASE || "http://localhost:4000";

function getToken() {
  return localStorage.getItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function signup(email: string, password: string) {
  const data = await request<{ token: string; user: User }>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("token", data.token);
  return data.user;
}

export async function login(email: string, password: string) {
  const data = await request<{ token: string; user: User }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("token", data.token);
  return data.user;
}

export async function me() {
  const data = await request<{ user: User }>("/auth/me");
  return data.user;
}

export async function startTrip(initialFuelLiters?: number) {
  return request<{ trip: Trip }>("/trips/start", {
    method: "POST",
    body: JSON.stringify({ initialFuelLiters }),
  });
}
export async function addPoint(lat: number, lng: number) {
  return request<{ point: TripPoint; distanceAdded: number; total: number }>(
    "/trips/point",
    { method: "POST", body: JSON.stringify({ lat, lng }) }
  );
}
export async function stopTrip(finalFuelLiters?: number) {
  return request<{ trip: Trip }>("/trips/stop", {
    method: "POST",
    body: JSON.stringify({ finalFuelLiters }),
  });
}
export async function activeTrip() {
  return request<{ active: Trip | null; points: TripPoint[] }>("/trips/active");
}

export async function fuelSnapshot(fuelLiters: number) {
  return request<{ ok: true }>("/fuel/snapshot", {
    method: "POST",
    body: JSON.stringify({ fuelLiters }),
  });
}
export async function fuelStats() {
  return request<FuelStats>("/fuel/stats");
}

export function logout() {
  localStorage.removeItem("token");
}
