import pytest
import pytest_asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_database, set_db_path, get_db
from app.calc import haversine_km, compute_consumption_stats, record_fuel_snapshot
import aiosqlite


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up in-memory database for tests."""
    set_db_path(":memory:")


@pytest.mark.asyncio
async def test_haversine_km_paris_london():
    """Test Haversine distance calculation between Paris and London."""
    # Paris (48.8566, 2.3522) London (51.5074, -0.1278) ~343 km (straight line)
    d = haversine_km(48.8566, 2.3522, 51.5074, -0.1278)
    assert d > 330
    assert d < 360


@pytest.mark.asyncio
async def test_consumption_stats_no_trips():
    """Test consumption stats with no trips."""
    await init_database()
    
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Create tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.execute("""
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fuel_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                fuel_liters REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        await db.commit()
        
        stats = await compute_consumption_stats(db, 999)  # user with no data
        assert stats.samples == 0
        assert stats.avgLitersPer100Km is None


@pytest.mark.asyncio
async def test_consumption_stats_with_trips():
    """Test consumption stats with trip data."""
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Create tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.execute("""
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fuel_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                fuel_liters REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        await db.commit()
        
        # Create user
        await db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("test@example.com", "hash")
        )
        await db.commit()
        
        async with db.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)) as cursor:
            row = await cursor.fetchone()
            user_id = row[0]
        
        # Trip 1: 100 km, consumed 5 L (50 -> 45)
        await db.execute(
            '''INSERT INTO trips (user_id, started_at, ended_at, initial_fuel_liters, final_fuel_liters, total_distance_km) 
               VALUES (?, datetime("now","-2 day"), datetime("now","-2 day","+1 hour"), ?, ?, ?)''',
            (user_id, 50, 45, 100)
        )
        
        # Trip 2: 120 km, consumed 6 L (60 -> 54)
        await db.execute(
            '''INSERT INTO trips (user_id, started_at, ended_at, initial_fuel_liters, final_fuel_liters, total_distance_km) 
               VALUES (?, datetime("now","-1 day"), datetime("now","-1 day","+2 hour"), ?, ?, ?)''',
            (user_id, 60, 54, 120)
        )
        await db.commit()
        
        # Current fuel snapshot: 30 L
        await record_fuel_snapshot(db, user_id, 30)
        
        stats = await compute_consumption_stats(db, user_id)
        assert stats.samples >= 2
        # Each trip 5 L / 100 km => 5 L/100km
        assert stats.avgLitersPer100Km is not None
        assert stats.avgLitersPer100Km > 4.8
        assert stats.avgLitersPer100Km < 5.2
        # Projected range = fuel / (L/km) where L/km = 0.05 -> 600 km
        assert stats.projectedRangeKm is not None
        assert stats.projectedRangeKm > 580
        assert stats.projectedRangeKm < 620
        # Days left should be positive
        assert stats.projectedDaysLeft is not None
        assert stats.projectedDaysLeft > 0
