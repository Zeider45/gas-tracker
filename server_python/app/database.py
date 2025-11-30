import os
import aiosqlite
from pathlib import Path
from .config import DB_PATH

# Global connection variable
_db_path: str = DB_PATH


def get_db_path() -> str:
    return _db_path


def set_db_path(path: str):
    global _db_path
    _db_path = path


async def get_db():
    """Get a database connection."""
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()


async def init_database():
    """Initialize the database schema."""
    db_path = get_db_path()
    
    # Ensure directory exists (except for :memory: database)
    if db_path != ":memory:":
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        
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
            CREATE TABLE IF NOT EXISTS trip_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                FOREIGN KEY(trip_id) REFERENCES trips(id) ON DELETE CASCADE
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
        
        # Create indexes
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_trip_points_trip_id ON trip_points(trip_id);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_fuel_snapshots_user_id ON fuel_snapshots(user_id);"
        )
        
        await db.commit()
        
    print(f"SQLite DB initialized at {db_path}")
