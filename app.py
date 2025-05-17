from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend2.routes import inventory, auth, orders
from backend2.database import init_db
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get allowed origins from environment variable or use defaults
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
# Split multiple URLs if provided as comma-separated string
allowed_origins = [origin.strip() for origin in FRONTEND_URL.split(",")]

# Add your Netlify domain to allowed origins
if "https://stockpulse.netlify.app" not in allowed_origins:
    allowed_origins.append("https://stockpulse.netlify.app")

logger.info(f"CORS allowed origins: {allowed_origins}")

# Improved CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Use dynamic origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["*"],  # Expose headers to JavaScript
    max_age=600,  # Cache preflight requests for 10 minutes
)

@app.on_event("startup")
async def startup_event():
    try:
        # Initialize database
        init_db()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

# Include routers
app.include_router(inventory.router)
app.include_router(auth.router)
app.include_router(orders.router)

@app.get("/")
def read_root():
    return {"message": "FastAPI Inventory Backend is running"}
