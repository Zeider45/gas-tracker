import os
from dotenv import load_dotenv

load_dotenv()

# Server settings
PORT = int(os.getenv("PORT", "4000"))
HOST = os.getenv("HOST", "0.0.0.0")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

# Database settings
DB_PATH = os.getenv("DB_PATH", "./data/gastracker.db")
