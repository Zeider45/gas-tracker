import math
from typing import Optional
import aiosqlite
from .models import FuelStats


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


def safe_divide(a: float, b: float) -> Optional[float]:
    """Safely divide two numbers, returning None if division is not possible."""
    if not math.isfinite(a) or not math.isfinite(b) or b == 0:
        return None
    return a / b


async def get_current_fuel(db: aiosqlite.Connection, user_id: int) -> Optional[float]:
    """Get the most recent fuel snapshot for a user."""
    async with db.execute(
        "SELECT fuel_liters FROM fuel_snapshots WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return float(row["fuel_liters"]) if row else None


async def compute_consumption_stats(db: aiosqlite.Connection, user_id: int) -> FuelStats:
    """Compute fuel consumption statistics for a user."""
    current_fuel_liters = await get_current_fuel(db, user_id)
    
    # Pull last 20 finished trips with fuel data
    async with db.execute(
        """SELECT id, initial_fuel_liters, final_fuel_liters, total_distance_km, started_at, ended_at
           FROM trips
           WHERE user_id = ? AND ended_at IS NOT NULL 
             AND initial_fuel_liters IS NOT NULL 
             AND final_fuel_liters IS NOT NULL 
             AND total_distance_km > 0
           ORDER BY ended_at DESC LIMIT 20""",
        (user_id,)
    ) as cursor:
        trips = await cursor.fetchall()
    
    total_distance = 0.0
    total_fuel_consumed = 0.0
    total_days = 0.0
    
    for trip in trips:
        consumed = float(trip["initial_fuel_liters"]) - float(trip["final_fuel_liters"])
        if consumed <= 0:
            continue  # ignore invalid
        
        dist = float(trip["total_distance_km"])
        if dist <= 0:
            continue
        
        total_distance += dist
        total_fuel_consumed += consumed
        
        # Calculate trip duration
        from datetime import datetime
        start = datetime.fromisoformat(trip["started_at"].replace('Z', '+00:00'))
        end = datetime.fromisoformat(trip["ended_at"].replace('Z', '+00:00'))
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
    
    return FuelStats(
        currentFuelLiters=current_fuel_liters,
        avgLitersPer100Km=avg_liters_per_100km,
        avgKmPerDay=avg_km_per_day,
        projectedRangeKm=projected_range_km,
        projectedDaysLeft=projected_days_left,
        samples=samples,
    )


async def record_fuel_snapshot(db: aiosqlite.Connection, user_id: int, fuel_liters: float):
    """Record a new fuel snapshot for a user."""
    await db.execute(
        "INSERT INTO fuel_snapshots (user_id, fuel_liters) VALUES (?, ?)",
        (user_id, fuel_liters)
    )
    await db.commit()
