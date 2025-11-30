from fastapi import APIRouter, Depends, HTTPException, status
import aiosqlite

from ..database import get_db
from ..auth import get_current_user
from ..models import AuthUser, FuelSnapshotCreate, FuelStats
from ..calc import compute_consumption_stats, record_fuel_snapshot

router = APIRouter(prefix="/fuel", tags=["fuel"])


@router.post("/snapshot", status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    snapshot_data: FuelSnapshotCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Record a fuel snapshot."""
    if snapshot_data.fuelLiters < 0 or snapshot_data.fuelLiters > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation", "details": [{"msg": "fuelLiters must be between 0 and 200"}]}
        )
    
    await record_fuel_snapshot(db, current_user.id, snapshot_data.fuelLiters)
    return {"ok": True}


@router.get("/stats", response_model=FuelStats)
async def get_stats(
    current_user: AuthUser = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get fuel consumption statistics."""
    stats = await compute_consumption_stats(db, current_user.id)
    return stats
