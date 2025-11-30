from fastapi import APIRouter, Depends, HTTPException, status
import aiosqlite

from ..database import get_db
from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..models import UserCreate, TokenResponse, UserResponse, AuthUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Register a new user."""
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation", "details": [{"msg": "Password must be at least 6 characters"}]}
        )
    
    password_hash = hash_password(user_data.password)
    
    try:
        cursor = await db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (user_data.email, password_hash)
        )
        await db.commit()
        user_id = cursor.lastrowid
    except aiosqlite.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "email_taken"}
        )
    
    token = create_access_token(user_id, user_data.email)
    return TokenResponse(
        token=token,
        user=UserResponse(id=user_id, email=user_data.email)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Login an existing user."""
    async with db.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?",
        (user_data.email,)
    ) as cursor:
        row = await cursor.fetchone()
    
    if not row or not verify_password(user_data.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials"}
        )
    
    token = create_access_token(row["id"], row["email"])
    return TokenResponse(
        token=token,
        user=UserResponse(id=row["id"], email=row["email"])
    )


@router.get("/me")
async def get_me(current_user: AuthUser = Depends(get_current_user)):
    """Get the current authenticated user."""
    return {"user": current_user}
