from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import PORT, HOST
from .database import init_database
from .routes import auth, trips, fuel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_database()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Gas Tracker API",
    description="API for tracking trips and fuel consumption",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins for mobile/LAN access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    import time
    return {"status": "ok", "timestamp": int(time.time() * 1000)}


# Include routers
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(fuel.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
