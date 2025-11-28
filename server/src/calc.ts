import { db } from "./db";

export interface ConsumptionStats {
  currentFuelLiters: number | null;
  avgLitersPer100Km: number | null; // L/100km
  avgKmPerDay: number | null;
  projectedRangeKm: number | null;
  projectedDaysLeft: number | null;
  samples: number; // number of trips included
}

function safeDivide(a: number, b: number): number | null {
  if (!isFinite(a) || !isFinite(b) || b === 0) return null;
  return a / b;
}

export async function getCurrentFuel(userId: number): Promise<number | null> {
  return new Promise((resolve, reject) => {
    db.get(
      "SELECT fuel_liters FROM fuel_snapshots WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
      [userId],
      (err, row: any) => {
        if (err) return reject(err);
        resolve(row ? Number(row.fuel_liters) : null);
      }
    );
  });
}

export async function computeConsumptionStats(
  userId: number
): Promise<ConsumptionStats> {
  const currentFuelLiters = await getCurrentFuel(userId);
  // Pull last 20 finished trips with fuel data
  const trips: any[] = await new Promise((resolve, reject) => {
    db.all(
      `SELECT id, initial_fuel_liters, final_fuel_liters, total_distance_km, started_at, ended_at
       FROM trips
       WHERE user_id = ? AND ended_at IS NOT NULL AND initial_fuel_liters IS NOT NULL AND final_fuel_liters IS NOT NULL AND total_distance_km > 0
       ORDER BY ended_at DESC LIMIT 20`,
      [userId],
      (err, rows) => (err ? reject(err) : resolve(rows))
    );
  });

  let totalDistance = 0;
  let totalFuelConsumed = 0; // liters
  let totalDays = 0;

  for (const t of trips) {
    const consumed =
      Number(t.initial_fuel_liters) - Number(t.final_fuel_liters);
    if (consumed <= 0) continue; // ignore invalid
    const dist = Number(t.total_distance_km);
    if (dist <= 0) continue;
    totalDistance += dist;
    totalFuelConsumed += consumed;
    const start = new Date(t.started_at).getTime();
    const end = new Date(t.ended_at).getTime();
    const durDays = (end - start) / (1000 * 60 * 60 * 24);
    totalDays += Math.max(durDays, dist / 500); // fallback minimal duration
  }

  const samples = trips.length;
  const litersPerKm = safeDivide(totalFuelConsumed, totalDistance); // L/km
  const avgLitersPer100Km = litersPerKm === null ? null : litersPerKm * 100;
  const avgKmPerDay = safeDivide(totalDistance, totalDays);
  const projectedRangeKm =
    litersPerKm && currentFuelLiters !== null
      ? currentFuelLiters / litersPerKm
      : null;
  const avgFuelPerDay = safeDivide(totalFuelConsumed, totalDays);
  const projectedDaysLeft =
    avgFuelPerDay && currentFuelLiters !== null
      ? currentFuelLiters / avgFuelPerDay
      : null;

  return {
    currentFuelLiters,
    avgLitersPer100Km,
    avgKmPerDay,
    projectedRangeKm,
    projectedDaysLeft,
    samples,
  };
}

export async function recordFuelSnapshot(
  userId: number,
  fuelLiters: number
): Promise<void> {
  return new Promise((resolve, reject) => {
    const stmt = db.prepare(
      "INSERT INTO fuel_snapshots (user_id, fuel_liters) VALUES (?, ?)"
    );
    stmt.run(userId, fuelLiters, (err: Error | null) =>
      err ? reject(err) : resolve()
    );
  });
}
