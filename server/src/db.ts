import path from "path";
import fs from "fs";
import sqlite3 from "sqlite3";

sqlite3.verbose();

const dbPath =
  process.env.DB_PATH || path.join(process.cwd(), "data", "gas-tracker.db");

// Ensure directory exists
const dir = path.dirname(dbPath);
if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}

export const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error("Failed to open database", err);
  } else {
    console.log("SQLite DB opened at", dbPath);
  }
});

export function initDatabase(): Promise<void> {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      db.run("PRAGMA foreign_keys = ON;");

      db.run(
        `CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );`
      );

      db.run(
        `CREATE TABLE IF NOT EXISTS trips (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          ended_at DATETIME,
          initial_fuel_liters REAL,
          final_fuel_liters REAL,
          total_distance_km REAL DEFAULT 0,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );`
      );

      db.run(
        `CREATE TABLE IF NOT EXISTS trip_points (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          trip_id INTEGER NOT NULL,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
          lat REAL NOT NULL,
          lng REAL NOT NULL,
          FOREIGN KEY(trip_id) REFERENCES trips(id) ON DELETE CASCADE
        );`
      );

      db.run(
        `CREATE TABLE IF NOT EXISTS fuel_snapshots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
          fuel_liters REAL NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );`
      );

      // Create indexes to speed up queries
      db.run(
        `CREATE INDEX IF NOT EXISTS idx_trip_points_trip_id ON trip_points(trip_id);`
      );
      db.run(
        `CREATE INDEX IF NOT EXISTS idx_fuel_snapshots_user_id ON fuel_snapshots(user_id);`
      );

      db.get(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users';",
        (e) => {
          if (e) return reject(e);
          resolve();
        }
      );
    });
  });
}
