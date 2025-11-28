import React, { createContext, useContext, useState, useEffect } from "react";
import { User, TripPoint, Trip, FuelStats } from "./types";
import { me, activeTrip, fuelStats, logout } from "./api";

interface AppState {
  user: User | null;
  setUser(u: User | null): void;
  trip: Trip | null;
  points: TripPoint[];
  stats: FuelStats | null;
  refreshTrip(): Promise<void>;
  refreshStats(): Promise<void>;
  doLogout(): void;
  theme: string;
  toggleTheme(): void;
}

const Ctx = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [points, setPoints] = useState<TripPoint[]>([]);
  const [stats, setStats] = useState<FuelStats | null>(null);
  const [theme, setTheme] = useState<string>("dark");

  useEffect(() => {
    (async () => {
      try {
        const u = await me();
        setUser(u);
      } catch {}
    })();
  }, []);

  async function refreshTrip() {
    if (!user) return;
    try {
      const data = await activeTrip();
      setTrip(data.active);
      setPoints(data.points || []);
    } catch {}
  }

  async function refreshStats() {
    if (!user) return;
    try {
      const s = await fuelStats();
      setStats(s);
    } catch {}
  }

  function doLogout() {
    logout();
    setUser(null);
    setTrip(null);
    setPoints([]);
    setStats(null);
  }

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
  }

  const value: AppState = {
    user,
    setUser,
    trip,
    points,
    stats,
    refreshTrip,
    refreshStats,
    doLogout,
    theme,
    toggleTheme,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
};

export function useApp() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useApp must be used within AppProvider");
  return v;
}
