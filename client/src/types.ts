export interface User {
  id: number;
  email: string;
}
export interface Trip {
  id: number;
  user_id: number;
  started_at: string;
  ended_at: string | null;
  initial_fuel_liters: number | null;
  final_fuel_liters: number | null;
  total_distance_km: number;
}
export interface TripPoint {
  id: number;
  trip_id: number;
  timestamp: string;
  lat: number;
  lng: number;
}
export interface FuelStats {
  currentFuelLiters: number | null;
  avgLitersPer100Km: number | null;
  avgKmPerDay: number | null;
  projectedRangeKm: number | null;
  projectedDaysLeft: number | null;
  samples: number;
}
