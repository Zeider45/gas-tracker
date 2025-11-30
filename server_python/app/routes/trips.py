from fastapi import APIRouter, Depends, HTTPException, status
import aiosqlite

from ..database import get_db
from ..auth import get_current_user
from ..models import (
    AuthUser, TripCreate, TripStop, TripPointCreate,
    TripResponse, ActiveTripResponse, PointAddedResponse
)
from ..trips import get_active_trip, start_trip, add_point, stop_trip, list_trip_points

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/active", response_model=ActiveTripResponse)
async def get_active(
    current_user: AuthUser = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get the active trip for the current user."""
    trip = await get_active_trip(db, current_user.id)
    
    if not trip:
        return ActiveTripResponse(active=None, points=[])
    
    points = await list_trip_points(db, trip.id, 50)
    return ActiveTripResponse(active=trip, points=points)


@router.post("/start", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def start_new_trip(
    trip_data: TripCreate = TripCreate(),
    current_user: AuthUser = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Start a new trip."""
    existing = await get_active_trip(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "trip_active"}
        )
    
    trip = await start_trip(db, current_user.id, trip_data.initialFuelLiters)
    return TripResponse(trip=trip)


@router.post("/point", response_model=PointAddedResponse)
async def add_trip_point(
    point_data: TripPointCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Add a point to the active trip."""
    if point_data.lat < -90 or point_data.lat > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation", "details": [{"msg": "lat must be between -90 and 90"}]}
        )
    if point_data.lng < -180 or point_data.lng > 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation", "details": [{"msg": "lng must be between -180 and 180"}]}
        )
    
    trip = await get_active_trip(db, current_user.id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "no_active_trip"}
        )
    
    point, distance_added, total = await add_point(db, trip.id, point_data.lat, point_data.lng)
    return PointAddedResponse(point=point, distanceAdded=distance_added, total=total)


@router.post("/stop", response_model=TripResponse)
async def stop_active_trip(
    trip_data: TripStop = TripStop(),
    current_user: AuthUser = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Stop the active trip."""
    trip = await get_active_trip(db, current_user.id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "no_active_trip"}
        )
    
    updated = await stop_trip(db, trip.id, trip_data.finalFuelLiters)
    return TripResponse(trip=updated)
