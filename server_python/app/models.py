from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Auth models
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


class AuthUser(BaseModel):
    id: int
    email: str


# Trip models
class TripCreate(BaseModel):
    initialFuelLiters: Optional[float] = None


class TripStop(BaseModel):
    finalFuelLiters: Optional[float] = None


class TripPointCreate(BaseModel):
    lat: float
    lng: float


class TripPoint(BaseModel):
    id: int
    trip_id: int
    timestamp: str
    lat: float
    lng: float


class Trip(BaseModel):
    id: int
    user_id: int
    started_at: str
    ended_at: Optional[str]
    initial_fuel_liters: Optional[float]
    final_fuel_liters: Optional[float]
    total_distance_km: float


class TripResponse(BaseModel):
    trip: Trip


class ActiveTripResponse(BaseModel):
    active: Optional[Trip]
    points: List[TripPoint] = []


class PointAddedResponse(BaseModel):
    point: TripPoint
    distanceAdded: float
    total: float


# Fuel models
class FuelSnapshotCreate(BaseModel):
    fuelLiters: float


class FuelStats(BaseModel):
    currentFuelLiters: Optional[float]
    avgLitersPer100Km: Optional[float]
    avgKmPerDay: Optional[float]
    projectedRangeKm: Optional[float]
    projectedDaysLeft: Optional[float]
    samples: int
