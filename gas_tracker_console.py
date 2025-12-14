#!/usr/bin/env python3
"""
Gas Tracker Console Application
Console-only version for tracking trips and fuel consumption.
"""

import sqlite3
import csv
import sys
import os
from datetime import datetime
from pathlib import Path
import math


# Database path
DB_PATH = "./data/gastracker_console.db"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Haversine distance between two points in kilometers."""
    R = 6371  # Earth's radius in km
    
    def to_rad(deg: float) -> float:
        return deg * math.pi / 180
    
    d_lat = to_rad(lat2 - lat1)
    d_lon = to_rad(lon2 - lon1)
    
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(to_rad(lat1)) * math.cos(to_rad(lat2)) * 
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def safe_divide(a: float, b: float):
    """Safely divide two numbers, returning None if division is not possible."""
    if not math.isfinite(a) or not math.isfinite(b) or b == 0:
        return None
    return a / b


def init_database():
    """Initialize the database schema."""
    db_dir = Path(DB_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            initial_fuel_liters REAL,
            final_fuel_liters REAL,
            total_distance_km REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trip_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            FOREIGN KEY(trip_id) REFERENCES trips(id) ON DELETE CASCADE
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fuel_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            fuel_liters REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    
    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_trip_points_trip_id ON trip_points(trip_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_fuel_snapshots_user_id ON fuel_snapshots(user_id);"
    )
    
    conn.commit()
    conn.close()
    
    print(f"✓ Base de datos inicializada en {DB_PATH}")


def get_or_create_default_user():
    """Get or create default user for console application."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", ("console@user.local",))
    row = cursor.fetchone()
    
    if row:
        user_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("console@user.local", "console")
        )
        conn.commit()
        user_id = cursor.lastrowid
        print("✓ Usuario por defecto creado")
    
    conn.close()
    return user_id


def get_active_trip(user_id: int):
    """Get the active trip for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM trips WHERE user_id = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "started_at": row[2],
            "ended_at": row[3],
            "initial_fuel_liters": row[4],
            "final_fuel_liters": row[5],
            "total_distance_km": row[6] or 0,
        }
    return None


def start_trip(user_id: int, initial_fuel: float = None):
    """Start a new trip for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO trips (user_id, initial_fuel_liters) VALUES (?, ?)",
        (user_id, initial_fuel)
    )
    conn.commit()
    trip_id = cursor.lastrowid
    conn.close()
    
    print(f"✓ Viaje iniciado (ID: {trip_id})")
    if initial_fuel:
        print(f"  Combustible inicial: {initial_fuel} litros")
    return trip_id


def add_distance_to_trip(trip_id: int, distance_km: float):
    """Add distance to a trip manually."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE trips SET total_distance_km = total_distance_km + ? WHERE id = ?",
        (distance_km, trip_id)
    )
    conn.commit()
    
    cursor.execute("SELECT total_distance_km FROM trips WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    total = row[0] if row else 0
    
    conn.close()
    
    print(f"✓ Distancia agregada: {distance_km:.2f} km")
    print(f"  Distancia total: {total:.2f} km")
    return total


def stop_trip(trip_id: int, final_fuel: float = None):
    """Stop a trip and return the updated trip."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE trips SET ended_at = CURRENT_TIMESTAMP, final_fuel_liters = ? WHERE id = ? AND ended_at IS NULL",
        (final_fuel, trip_id)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        trip = {
            "id": row[0],
            "user_id": row[1],
            "started_at": row[2],
            "ended_at": row[3],
            "initial_fuel_liters": row[4],
            "final_fuel_liters": row[5],
            "total_distance_km": row[6] or 0,
        }
        print(f"✓ Viaje finalizado (ID: {trip['id']})")
        print(f"  Distancia total: {trip['total_distance_km']:.2f} km")
        if final_fuel:
            print(f"  Combustible final: {final_fuel} litros")
        return trip
    return None


def add_fuel_snapshot(user_id: int, fuel_liters: float):
    """Record a new fuel snapshot for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO fuel_snapshots (user_id, fuel_liters) VALUES (?, ?)",
        (user_id, fuel_liters)
    )
    conn.commit()
    conn.close()
    
    print(f"✓ Snapshot de combustible registrado: {fuel_liters} litros")


def get_current_fuel(user_id: int):
    """Get the most recent fuel snapshot for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT fuel_liters FROM fuel_snapshots WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    return float(row[0]) if row else None


def compute_consumption_stats(user_id: int):
    """Compute fuel consumption statistics for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_fuel_liters = get_current_fuel(user_id)
    
    # Pull last 20 finished trips with fuel data
    cursor.execute(
        """SELECT id, initial_fuel_liters, final_fuel_liters, total_distance_km, started_at, ended_at
           FROM trips
           WHERE user_id = ? AND ended_at IS NOT NULL 
             AND initial_fuel_liters IS NOT NULL 
             AND final_fuel_liters IS NOT NULL 
             AND total_distance_km > 0
           ORDER BY ended_at DESC LIMIT 20""",
        (user_id,)
    )
    trips = cursor.fetchall()
    conn.close()
    
    total_distance = 0.0
    total_fuel_consumed = 0.0
    total_days = 0.0
    
    for trip in trips:
        consumed = float(trip[1]) - float(trip[2])
        if consumed <= 0:
            continue  # ignore invalid
        
        dist = float(trip[3])
        if dist <= 0:
            continue
        
        total_distance += dist
        total_fuel_consumed += consumed
        
        # Calculate trip duration
        start = datetime.fromisoformat(trip[4].replace('Z', '+00:00'))
        end = datetime.fromisoformat(trip[5].replace('Z', '+00:00'))
        dur_days = (end - start).total_seconds() / (60 * 60 * 24)
        total_days += max(dur_days, dist / 500)  # fallback minimal duration
    
    samples = len(trips)
    liters_per_km = safe_divide(total_fuel_consumed, total_distance)
    avg_liters_per_100km = liters_per_km * 100 if liters_per_km is not None else None
    avg_km_per_day = safe_divide(total_distance, total_days)
    
    projected_range_km = None
    if liters_per_km is not None and current_fuel_liters is not None:
        projected_range_km = current_fuel_liters / liters_per_km
    
    avg_fuel_per_day = safe_divide(total_fuel_consumed, total_days)
    projected_days_left = None
    if avg_fuel_per_day is not None and current_fuel_liters is not None:
        projected_days_left = current_fuel_liters / avg_fuel_per_day
    
    return {
        "currentFuelLiters": current_fuel_liters,
        "avgLitersPer100Km": avg_liters_per_100km,
        "avgKmPerDay": avg_km_per_day,
        "projectedRangeKm": projected_range_km,
        "projectedDaysLeft": projected_days_left,
        "samples": samples,
    }


def list_all_trips(user_id: int):
    """Get all trips for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM trips WHERE user_id = ? ORDER BY started_at DESC",
        (user_id,)
    )
    trips = cursor.fetchall()
    conn.close()
    
    return [{
        "id": row[0],
        "user_id": row[1],
        "started_at": row[2],
        "ended_at": row[3],
        "initial_fuel_liters": row[4],
        "final_fuel_liters": row[5],
        "total_distance_km": row[6] or 0,
    } for row in trips]


def export_trips_to_csv(user_id: int, filename: str = "trips_export.csv"):
    """Export all trips for the current user as CSV."""
    trips = list_all_trips(user_id)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers
        writer.writerow([
            "id",
            "user_id",
            "started_at",
            "ended_at",
            "initial_fuel_liters",
            "final_fuel_liters",
            "total_distance_km"
        ])
        
        # Write data rows
        for trip in trips:
            writer.writerow([
                trip["id"],
                trip["user_id"],
                trip["started_at"],
                trip["ended_at"] or "",
                trip["initial_fuel_liters"] if trip["initial_fuel_liters"] is not None else "",
                trip["final_fuel_liters"] if trip["final_fuel_liters"] is not None else "",
                trip["total_distance_km"]
            ])
    
    print(f"✓ Viajes exportados a {filename}")
    print(f"  Total de viajes: {len(trips)}")


def display_stats(user_id: int):
    """Display fuel consumption statistics."""
    stats = compute_consumption_stats(user_id)
    
    print("\n" + "="*50)
    print("  ESTADÍSTICAS DE CONSUMO")
    print("="*50)
    
    if stats["currentFuelLiters"] is not None:
        print(f"Combustible actual: {stats['currentFuelLiters']:.2f} litros")
    else:
        print("Combustible actual: No registrado")
    
    if stats["samples"] > 0:
        if stats["avgLitersPer100Km"] is not None:
            print(f"Consumo promedio: {stats['avgLitersPer100Km']:.2f} L/100km")
        
        if stats["avgKmPerDay"] is not None:
            print(f"Km promedio por día: {stats['avgKmPerDay']:.2f} km/día")
        
        if stats["projectedRangeKm"] is not None:
            print(f"Rango proyectado: {stats['projectedRangeKm']:.2f} km")
        
        if stats["projectedDaysLeft"] is not None:
            print(f"Días restantes: {stats['projectedDaysLeft']:.2f} días")
        
        print(f"Basado en {stats['samples']} viaje(s)")
    else:
        print("No hay suficientes datos para calcular estadísticas")
    
    print("="*50 + "\n")


def display_trips(user_id: int):
    """Display all trips."""
    trips = list_all_trips(user_id)
    
    if not trips:
        print("\nNo hay viajes registrados.\n")
        return
    
    print("\n" + "="*50)
    print("  HISTORIAL DE VIAJES")
    print("="*50)
    
    for trip in trips:
        status = "EN CURSO" if trip["ended_at"] is None else "FINALIZADO"
        print(f"\nID: {trip['id']} - {status}")
        print(f"  Inicio: {trip['started_at']}")
        if trip['ended_at']:
            print(f"  Fin: {trip['ended_at']}")
        print(f"  Distancia: {trip['total_distance_km']:.2f} km")
        if trip['initial_fuel_liters'] is not None:
            print(f"  Combustible inicial: {trip['initial_fuel_liters']:.2f} L")
        if trip['final_fuel_liters'] is not None:
            print(f"  Combustible final: {trip['final_fuel_liters']:.2f} L")
            if trip['initial_fuel_liters'] is not None:
                consumed = trip['initial_fuel_liters'] - trip['final_fuel_liters']
                print(f"  Combustible consumido: {consumed:.2f} L")
                if trip['total_distance_km'] > 0:
                    consumption = (consumed / trip['total_distance_km']) * 100
                    print(f"  Consumo: {consumption:.2f} L/100km")
    
    print("="*50 + "\n")


def read_float(prompt: str, allow_none: bool = False) -> float:
    """Read a float from user input."""
    while True:
        try:
            value = input(prompt).strip()
            if allow_none and value == "":
                return None
            return float(value)
        except ValueError:
            print("⚠ Por favor ingresa un número válido")


def main_menu():
    """Display main menu and handle user input."""
    print("\n" + "="*50)
    print("  GAS TRACKER - Versión Consola")
    print("="*50)
    print("1. Iniciar nuevo viaje")
    print("2. Agregar kilómetros al viaje activo")
    print("3. Finalizar viaje activo")
    print("4. Registrar snapshot de combustible")
    print("5. Ver estadísticas")
    print("6. Ver historial de viajes")
    print("7. Exportar viajes a CSV")
    print("0. Salir")
    print("="*50)
    
    choice = input("\nSelecciona una opción: ").strip()
    return choice


def main():
    """Main application loop."""
    print("\n" + "="*50)
    print("  Bienvenido a Gas Tracker Console")
    print("="*50 + "\n")
    
    # Initialize database
    init_database()
    
    # Get or create default user
    user_id = get_or_create_default_user()
    
    while True:
        choice = main_menu()
        
        if choice == "1":
            # Start new trip
            active = get_active_trip(user_id)
            if active:
                print("\n⚠ Ya tienes un viaje activo. Finalízalo antes de iniciar uno nuevo.\n")
                continue
            
            print("\n--- INICIAR VIAJE ---")
            initial_fuel = read_float("Combustible inicial en litros (Enter para omitir): ", allow_none=True)
            start_trip(user_id, initial_fuel)
            print()
        
        elif choice == "2":
            # Add kilometers
            active = get_active_trip(user_id)
            if not active:
                print("\n⚠ No hay un viaje activo. Inicia un viaje primero.\n")
                continue
            
            print("\n--- AGREGAR KILÓMETROS ---")
            print(f"Viaje activo: ID {active['id']}")
            print(f"Distancia actual: {active['total_distance_km']:.2f} km")
            
            distance = read_float("Kilómetros a agregar: ")
            if distance > 0:
                add_distance_to_trip(active['id'], distance)
            else:
                print("⚠ La distancia debe ser mayor a 0")
            print()
        
        elif choice == "3":
            # Stop trip
            active = get_active_trip(user_id)
            if not active:
                print("\n⚠ No hay un viaje activo para finalizar.\n")
                continue
            
            print("\n--- FINALIZAR VIAJE ---")
            print(f"Viaje activo: ID {active['id']}")
            print(f"Distancia total: {active['total_distance_km']:.2f} km")
            
            final_fuel = read_float("Combustible final en litros (Enter para omitir): ", allow_none=True)
            stop_trip(active['id'], final_fuel)
            print()
        
        elif choice == "4":
            # Add fuel snapshot
            print("\n--- REGISTRAR COMBUSTIBLE ---")
            fuel = read_float("Combustible actual en litros: ")
            if fuel > 0:
                add_fuel_snapshot(user_id, fuel)
            else:
                print("⚠ El combustible debe ser mayor a 0")
            print()
        
        elif choice == "5":
            # View stats
            display_stats(user_id)
        
        elif choice == "6":
            # View trips
            display_trips(user_id)
        
        elif choice == "7":
            # Export CSV
            print("\n--- EXPORTAR A CSV ---")
            filename = input("Nombre del archivo (Enter para 'trips_export.csv'): ").strip()
            if not filename:
                filename = "trips_export.csv"
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            export_trips_to_csv(user_id, filename)
            print()
        
        elif choice == "0":
            # Exit
            print("\n¡Hasta luego!\n")
            break
        
        else:
            print("\n⚠ Opción no válida. Por favor selecciona una opción del menú.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n¡Hasta luego!\n")
        sys.exit(0)
