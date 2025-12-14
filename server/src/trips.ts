import { db } from "./db";

export interface TripRow {
  id: number;
  user_id: number;
  started_at: string;
  ended_at: string | null;
  initial_fuel_liters: number | null;
  final_fuel_liters: number | null;
  total_distance_km: number;
}

export interface TripPointRow {
  id: number;
  trip_id: number;
  timestamp: string;
  lat: number;
  lng: number;
}

// Haversine distance (km)
export function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // km
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export function getActiveTrip(userId: number): Promise<TripRow | null> {
  return new Promise((resolve, reject) => {
    db.get(
      "SELECT * FROM trips WHERE user_id = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
      [userId],
      (err, row: any) => {
        if (err) return reject(err);
        resolve(row ? (row as TripRow) : null);
      }
    );
  });
}

export function startTrip(
  userId: number,
  initialFuel?: number
): Promise<TripRow> {
  return new Promise((resolve, reject) => {
    const stmt = db.prepare(
      "INSERT INTO trips (user_id, initial_fuel_liters) VALUES (?, ?)"
    );
    stmt.run(
      userId,
      initialFuel ?? null,
      function (this: any, err: Error | null) {
        if (err) return reject(err);
        db.get("SELECT * FROM trips WHERE id = ?", [this.lastID], (e, row) => {
          if (e) return reject(e);
          resolve(row as TripRow);
        });
      }
    );
  });
}

export async function addPoint(
  tripId: number,
  lat: number,
  lng: number
): Promise<{ point: TripPointRow; distanceAdded: number; total: number }> {
  // get last point
  const lastPoint: TripPointRow | null = await new Promise(
    (resolve, reject) => {
      db.get(
        "SELECT * FROM trip_points WHERE trip_id = ? ORDER BY timestamp DESC LIMIT 1",
        [tripId],
        (err, row: any) => {
          if (err) return reject(err);
          resolve(row ? (row as TripPointRow) : null);
        }
      );
    }
  );
  let distanceAdded = 0;
  if (lastPoint) {
    distanceAdded = haversineKm(lastPoint.lat, lastPoint.lng, lat, lng);
  }
  // insert new point
  const point: TripPointRow = await new Promise((resolve, reject) => {
    const stmt = db.prepare(
      "INSERT INTO trip_points (trip_id, lat, lng) VALUES (?, ?, ?)"
    );
    stmt.run(tripId, lat, lng, function (this: any, err: Error | null) {
      if (err) return reject(err);
      db.get(
        "SELECT * FROM trip_points WHERE id = ?",
        [this.lastID],
        (e, row) => {
          if (e) return reject(e);
          resolve(row as TripPointRow);
        }
      );
    });
  });
  if (distanceAdded > 0) {
    await new Promise((resolve, reject) => {
      db.run(
        "UPDATE trips SET total_distance_km = total_distance_km + ? WHERE id = ?",
        [distanceAdded, tripId],
        (err) => (err ? reject(err) : resolve(undefined))
      );
    });
  }
  const trip: TripRow = await new Promise((resolve, reject) => {
    db.get("SELECT * FROM trips WHERE id = ?", [tripId], (err, row) => {
      if (err) return reject(err);
      resolve(row as TripRow);
    });
  });
  return { point, distanceAdded, total: trip.total_distance_km };
}

export function stopTrip(tripId: number, finalFuel?: number): Promise<TripRow> {
  return new Promise((resolve, reject) => {
    db.run(
      "UPDATE trips SET ended_at = CURRENT_TIMESTAMP, final_fuel_liters = ? WHERE id = ? AND ended_at IS NULL",
      [finalFuel ?? null, tripId],
      (err) => {
        if (err) return reject(err);
        db.get("SELECT * FROM trips WHERE id = ?", [tripId], (e, row) => {
          if (e) return reject(e);
          resolve(row as TripRow);
        });
      }
    );
  });
}

export function listTripPoints(
  tripId: number,
  limit = 100
): Promise<TripPointRow[]> {
  return new Promise((resolve, reject) => {
    db.all(
      "SELECT * FROM trip_points WHERE trip_id = ? ORDER BY timestamp DESC LIMIT ?",
      [tripId, limit],
      (err, rows) => {
        if (err) return reject(err);
        resolve(rows as TripPointRow[]);
      }
    );
  });
}

export function getAllTrips(userId: number): Promise<TripRow[]> {
  return new Promise((resolve, reject) => {
    db.all(
      "SELECT * FROM trips WHERE user_id = ? ORDER BY started_at DESC",
      [userId],
      (err, rows) => {
        if (err) return reject(err);
        resolve(rows as TripRow[]);
      }
    );
  });
}

export function convertTripsToCSV(trips: TripRow[]): string {
  const headers = [
    "id",
    "user_id",
    "started_at",
    "ended_at",
    "initial_fuel_liters",
    "final_fuel_liters",
    "total_distance_km"
  ];
  
  const csvRows = [headers.join(",")];
  
  for (const trip of trips) {
    const row = [
      trip.id,
      trip.user_id,
      trip.started_at,
      trip.ended_at || "",
      trip.initial_fuel_liters ?? "",
      trip.final_fuel_liters ?? "",
      trip.total_distance_km
    ];
    csvRows.push(row.join(","));
  }
  
  return csvRows.join("\n");
}
