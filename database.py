from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
Base = declarative_base()

# Database URL - using environment variables for security
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Hrit")  # Replace with your actual MySQL root password
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "stockpulse")
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is provided (production), use it
# Otherwise use local MySQL connection
if DATABASE_URL:
    # Check if using PostgreSQL from external provider (like ElephantSQL)
    if DATABASE_URL.startswith('postgres://'):
        # SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    logger.info("Using production database")
else:
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    logger.info(f"Using local MySQL database at: {DB_HOST}")

# Create engine with pool_pre_ping to handle connection issues
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database, creating tables if they don't exist."""
    try:
        # Import models after Base is defined
        from . import models
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
