from typing import Optional, List, Tuple
import aiosqlite
from .models import Trip, TripPoint
from .calc import haversine_km


def row_to_trip(row) -> Trip:
    """Convert a database row to a Trip model."""
    return Trip(
        id=row["id"],
        user_id=row["user_id"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        initial_fuel_liters=row["initial_fuel_liters"],
        final_fuel_liters=row["final_fuel_liters"],
        total_distance_km=row["total_distance_km"] or 0,
    )


def row_to_trip_point(row) -> TripPoint:
    """Convert a database row to a TripPoint model."""
    return TripPoint(
        id=row["id"],
        trip_id=row["trip_id"],
        timestamp=row["timestamp"],
        lat=row["lat"],
        lng=row["lng"],
    )


async def get_active_trip(db: aiosqlite.Connection, user_id: int) -> Optional[Trip]:
    """Get the active trip for a user."""
    async with db.execute(
        "SELECT * FROM trips WHERE user_id = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row_to_trip(row) if row else None


async def start_trip(db: aiosqlite.Connection, user_id: int, initial_fuel: Optional[float] = None) -> Trip:
    """Start a new trip for a user."""
    cursor = await db.execute(
        "INSERT INTO trips (user_id, initial_fuel_liters) VALUES (?, ?)",
        (user_id, initial_fuel)
    )
    await db.commit()
    
    async with db.execute(
        "SELECT * FROM trips WHERE id = ?",
        (cursor.lastrowid,)
    ) as cursor:
        row = await cursor.fetchone()
        return row_to_trip(row)


async def add_point(
    db: aiosqlite.Connection, 
    trip_id: int, 
    lat: float, 
    lng: float
) -> Tuple[TripPoint, float, float]:
    """Add a point to a trip and return the point, distance added, and total distance."""
    # Get last point
    async with db.execute(
        "SELECT * FROM trip_points WHERE trip_id = ? ORDER BY timestamp DESC LIMIT 1",
        (trip_id,)
    ) as cursor:
        last_point_row = await cursor.fetchone()
    
    distance_added = 0.0
    if last_point_row:
        last_point = row_to_trip_point(last_point_row)
        distance_added = haversine_km(last_point.lat, last_point.lng, lat, lng)
    
    # Insert new point
    cursor = await db.execute(
        "INSERT INTO trip_points (trip_id, lat, lng) VALUES (?, ?, ?)",
        (trip_id, lat, lng)
    )
    await db.commit()
    
    # Get the inserted point
    async with db.execute(
        "SELECT * FROM trip_points WHERE id = ?",
        (cursor.lastrowid,)
    ) as cursor:
        point_row = await cursor.fetchone()
        point = row_to_trip_point(point_row)
    
    # Update total distance if needed
    if distance_added > 0:
        await db.execute(
            "UPDATE trips SET total_distance_km = total_distance_km + ? WHERE id = ?",
            (distance_added, trip_id)
        )
        await db.commit()
    
    # Get updated trip
    async with db.execute(
        "SELECT * FROM trips WHERE id = ?",
        (trip_id,)
    ) as cursor:
        trip_row = await cursor.fetchone()
        total = trip_row["total_distance_km"] or 0
    
    return point, distance_added, total


async def stop_trip(db: aiosqlite.Connection, trip_id: int, final_fuel: Optional[float] = None) -> Trip:
    """Stop a trip and return the updated trip."""
    await db.execute(
        "UPDATE trips SET ended_at = CURRENT_TIMESTAMP, final_fuel_liters = ? WHERE id = ? AND ended_at IS NULL",
        (final_fuel, trip_id)
    )
    await db.commit()
    
    async with db.execute(
        "SELECT * FROM trips WHERE id = ?",
        (trip_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row_to_trip(row)


async def list_trip_points(db: aiosqlite.Connection, trip_id: int, limit: int = 100) -> List[TripPoint]:
    """List points for a trip."""
    async with db.execute(
        "SELECT * FROM trip_points WHERE trip_id = ? ORDER BY timestamp DESC LIMIT ?",
        (trip_id, limit)
    ) as cursor:
        rows = await cursor.fetchall()
        return [row_to_trip_point(row) for row in rows]


async def get_all_trips(db: aiosqlite.Connection, user_id: int) -> List[Trip]:
    """Get all trips for a user."""
    async with db.execute(
        "SELECT * FROM trips WHERE user_id = ? ORDER BY started_at DESC",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [row_to_trip(row) for row in rows]


def convert_trips_to_csv(trips: List[Trip]) -> str:
    """Convert a list of trips to CSV format."""
    headers = [
        "id",
        "user_id",
        "started_at",
        "ended_at",
        "initial_fuel_liters",
        "final_fuel_liters",
        "total_distance_km"
    ]
    
    csv_rows = [",".join(headers)]
    
    for trip in trips:
        row = [
            str(trip.id),
            str(trip.user_id),
            trip.started_at,
            trip.ended_at or "",
            str(trip.initial_fuel_liters) if trip.initial_fuel_liters is not None else "",
            str(trip.final_fuel_liters) if trip.final_fuel_liters is not None else "",
            str(trip.total_distance_km)
        ]
        csv_rows.append(",".join(row))
    
    return "\n".join(csv_rows)
