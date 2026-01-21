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

# Try to import matplotlib for graphing feature
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# Configuration constants
DB_PATH = "./data/gastracker_console.db"
MAX_TRIPS_FOR_STATS = 20  # Number of recent trips to use for statistics
FALLBACK_KM_PER_DAY = 500  # Fallback value when trip duration is too short


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
        # For console version, use a simple placeholder hash (not used for authentication)
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("console@user.local", "not_used")
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
    
    # Pull last N finished trips with fuel data
    cursor.execute(
        """SELECT id, initial_fuel_liters, final_fuel_liters, total_distance_km, started_at, ended_at
           FROM trips
           WHERE user_id = ? AND ended_at IS NOT NULL 
             AND initial_fuel_liters IS NOT NULL 
             AND final_fuel_liters IS NOT NULL 
             AND total_distance_km > 0
           ORDER BY ended_at DESC LIMIT ?""",
        (user_id, MAX_TRIPS_FOR_STATS)
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
        # Handle datetime parsing - remove 'Z' suffix if present
        start_str = trip[4].replace('Z', '') if trip[4] else trip[4]
        end_str = trip[5].replace('Z', '') if trip[5] else trip[5]
        
        try:
            # Try parsing with timezone first (Python 3.11+)
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)
        except ValueError:
            # Fallback to strptime for older Python versions
            start = datetime.strptime(start_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(end_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        
        dur_days = (end - start).total_seconds() / (60 * 60 * 24)
        total_days += max(dur_days, dist / FALLBACK_KM_PER_DAY)
    
    samples = len(trips)
    liters_per_km = safe_divide(total_fuel_consumed, total_distance)
    # Calculate km/l instead of L/100km
    avg_km_per_liter = safe_divide(total_distance, total_fuel_consumed)
    avg_km_per_day = safe_divide(total_distance, total_days)
    
    projected_range_km = None
    if avg_km_per_liter is not None and current_fuel_liters is not None:
        projected_range_km = current_fuel_liters * avg_km_per_liter
    
    avg_fuel_per_day = safe_divide(total_fuel_consumed, total_days)
    projected_days_left = None
    if avg_fuel_per_day is not None and current_fuel_liters is not None:
        projected_days_left = current_fuel_liters / avg_fuel_per_day
    
    return {
        "currentFuelLiters": current_fuel_liters,
        "avgKmPerLiter": avg_km_per_liter,
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
        # Only show Range and Consumption in km/l
        if stats["avgKmPerLiter"] is not None:
            print(f"Consumo: {stats['avgKmPerLiter']:.2f} km/l")
        
        if stats["projectedRangeKm"] is not None:
            print(f"Autonomía Proyectada (Range): {stats['projectedRangeKm']:.2f} km")
        
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
                if trip['total_distance_km'] > 0 and consumed > 0:
                    consumption = trip['total_distance_km'] / consumed
                    print(f"  Consumo: {consumption:.2f} km/l")
    
    print("="*50 + "\n")


def get_trip_stats_history(user_id: int):
    """Get historical trip data for graphing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT id, ended_at, initial_fuel_liters, final_fuel_liters, total_distance_km
           FROM trips
           WHERE user_id = ? AND ended_at IS NOT NULL 
             AND initial_fuel_liters IS NOT NULL 
             AND final_fuel_liters IS NOT NULL 
             AND total_distance_km > 0
           ORDER BY ended_at ASC""",
        (user_id,)
    )
    trips = cursor.fetchall()
    conn.close()
    
    # Calculate stats for each trip
    trip_data = []
    for trip in trips:
        consumed = float(trip[2]) - float(trip[3])
        if consumed <= 0:
            continue
        
        dist = float(trip[4])
        if dist <= 0:
            continue
        
        # Calculate km/l for this trip using safe_divide
        km_per_liter = safe_divide(dist, consumed)
        if km_per_liter is None:
            continue
        
        # Parse date
        date_str = trip[1].replace('Z', '') if trip[1] else trip[1]
        try:
            date = datetime.fromisoformat(date_str)
        except ValueError:
            date = datetime.strptime(date_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        
        trip_data.append({
            'date': date,
            'km_per_liter': km_per_liter,
            'distance': dist,
        })
    
    return trip_data


def display_graphs(user_id: int):
    """Display graphs for Range and Consumption."""
    if not MATPLOTLIB_AVAILABLE:
        print("\n⚠ La funcionalidad de gráficos no está disponible.")
        print("   Instala matplotlib para habilitar gráficos:")
        print("   pip install matplotlib")
        print()
        return
    
    # Get historical data
    trip_data = get_trip_stats_history(user_id)
    
    if not trip_data:
        print("\n⚠ No hay suficientes datos para mostrar gráficos.\n")
        return
    
    # Get current fuel for range calculation
    current_fuel = get_current_fuel(user_id)
    
    # Extract data for plotting
    dates = [trip['date'] for trip in trip_data]
    km_per_liter = [trip['km_per_liter'] for trip in trip_data]
    
    # Calculate projected range for each historical trip based on fuel after that trip
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, ended_at, final_fuel_liters
           FROM trips
           WHERE user_id = ? AND ended_at IS NOT NULL 
             AND final_fuel_liters IS NOT NULL
           ORDER BY ended_at ASC""",
        (user_id,)
    )
    fuel_snapshots = {row[0]: float(row[2]) for row in cursor.fetchall()}
    conn.close()
    
    # Get trip IDs for alignment
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id
           FROM trips
           WHERE user_id = ? AND ended_at IS NOT NULL 
             AND initial_fuel_liters IS NOT NULL 
             AND final_fuel_liters IS NOT NULL 
             AND total_distance_km > 0
           ORDER BY ended_at ASC""",
        (user_id,)
    )
    trip_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Calculate projected ranges using correct fuel levels
    projected_ranges = []
    for i, trip in enumerate(trip_data):
        if i < len(trip_ids) and trip_ids[i] in fuel_snapshots:
            fuel = fuel_snapshots[trip_ids[i]]
            projected_range = fuel * trip['km_per_liter']
            projected_ranges.append(projected_range)
        elif current_fuel:
            # Use current fuel as fallback
            projected_range = current_fuel * trip['km_per_liter']
            projected_ranges.append(projected_range)
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle('Estadísticas de Combustible', fontsize=16, fontweight='bold')
    
    # Plot 1: Consumo (km/l)
    ax1.plot(dates, km_per_liter, marker='o', linestyle='-', linewidth=2, markersize=6, color='#2ecc71')
    ax1.set_xlabel('Fecha', fontsize=12)
    ax1.set_ylabel('km/l', fontsize=12)
    ax1.set_title('Consumo (km/l)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Autonomía Proyectada (Range)
    if projected_ranges:
        ax2.plot(dates[:len(projected_ranges)], projected_ranges, marker='s', linestyle='-', linewidth=2, markersize=6, color='#3498db')
        ax2.set_xlabel('Fecha', fontsize=12)
        ax2.set_ylabel('km', fontsize=12)
        ax2.set_title('Autonomía Proyectada (Range)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    print("\n✓ Mostrando gráficos...")
    print("  Cierra la ventana de gráficos para continuar.\n")
    
    plt.show()



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
    print("8. Ver gráficos de Range y Consumo")
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
        
        elif choice == "8":
            # Display graphs
            display_graphs(user_id)
        
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
