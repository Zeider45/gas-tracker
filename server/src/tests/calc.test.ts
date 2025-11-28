import { describe, it, expect, beforeAll } from "vitest";

process.env.DB_PATH = ":memory:"; // use in-memory DB for tests

import { initDatabase, db } from "../db";
import { haversineKm } from "../trips";
import { computeConsumptionStats, recordFuelSnapshot } from "../calc";

function run(sql: string, params: any[] = []) {
  return new Promise<void>((resolve, reject) => {
    db.run(sql, params, (err) => (err ? reject(err) : resolve()));
  });
}

beforeAll(async () => {
  await initDatabase();
});

describe("haversineKm", () => {
  it("computes distance close to known city pair (Paris-London)", () => {
    // Paris (48.8566, 2.3522) London (51.5074, -0.1278) ~343 km (straight line)
    const d = haversineKm(48.8566, 2.3522, 51.5074, -0.1278);
    expect(d).toBeGreaterThan(330);
    expect(d).toBeLessThan(360);
  });
});

describe("computeConsumptionStats", () => {
  it("returns null-ish values when no trips", async () => {
    const stats = await computeConsumptionStats(999); // user with no data
    expect(stats.samples).toBe(0);
    expect(stats.avgLitersPer100Km).toBeNull();
  });

  it("computes averages and projections", async () => {
    // create user
    const uniqueEmail = `t_${Date.now()}_${Math.random()
      .toString(36)
      .slice(2)}@example.com`;
    await run("INSERT INTO users (email, password_hash) VALUES (?, ?)", [
      uniqueEmail,
      "hash",
    ]);
    const userId = await new Promise<number>((resolve, reject) => {
      db.get(
        "SELECT id FROM users WHERE email = ?",
        [uniqueEmail],
        (e, row: any) => {
          if (e) return reject(e);
          resolve(row.id);
        }
      );
    });

    // Trip 1: 100 km, consumed 5 L (50 -> 45)
    await run(
      'INSERT INTO trips (user_id, started_at, ended_at, initial_fuel_liters, final_fuel_liters, total_distance_km) VALUES (?, datetime("now","-2 day"), datetime("now","-2 day","+1 hour"), ?, ?, ?)',
      [userId, 50, 45, 100]
    );
    // Trip 2: 120 km, consumed 6 L (60 -> 54)
    await run(
      'INSERT INTO trips (user_id, started_at, ended_at, initial_fuel_liters, final_fuel_liters, total_distance_km) VALUES (?, datetime("now","-1 day"), datetime("now","-1 day","+2 hour"), ?, ?, ?)',
      [userId, 60, 54, 120]
    );
    // Current fuel snapshot: 30 L
    await recordFuelSnapshot(userId, 30);

    const stats = await computeConsumptionStats(userId);
    expect(stats.samples).toBeGreaterThanOrEqual(2);
    // Each trip 5 L / 100 km => 5 L/100km
    expect(stats.avgLitersPer100Km).toBeGreaterThan(4.8);
    expect(stats.avgLitersPer100Km).toBeLessThan(5.2);
    // Projected range = fuel / (L/km) where L/km = 0.05 -> 600 km
    expect(stats.projectedRangeKm).toBeGreaterThan(580);
    expect(stats.projectedRangeKm).toBeLessThan(620);
    // Days left should be positive
    expect(stats.projectedDaysLeft).toBeGreaterThan(0);
  });
});
