import os
import sys
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database URL - using environment variables for security
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Hrit")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "stockpulse")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

def migrate_db():
    """Add missing columns to the orders table."""
    try:
        # Create engine
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        # Check if the columns already exist
        with engine.connect() as connection:
            result = connection.execute(text("SHOW COLUMNS FROM orders"))
            columns = [row[0] for row in result]
            
            logger.info(f"Existing columns: {columns}")
            
            # Add missing supplier column
            if 'supplier' not in columns:
                logger.info("Adding 'supplier' column to orders table")
                connection.execute(text("ALTER TABLE orders ADD COLUMN supplier VARCHAR(100) NULL"))
                logger.info("Added 'supplier' column")
            
            # Add missing expected_delivery_date column
            if 'expected_delivery_date' not in columns:
                logger.info("Adding 'expected_delivery_date' column to orders table")
                connection.execute(text("ALTER TABLE orders ADD COLUMN expected_delivery_date DATETIME NULL"))
                logger.info("Added 'expected_delivery_date' column")
            
            # Add missing notes column
            if 'notes' not in columns:
                logger.info("Adding 'notes' column to orders table")
                connection.execute(text("ALTER TABLE orders ADD COLUMN notes VARCHAR(500) NULL"))
                logger.info("Added 'notes' column")
            
            # Add missing is_purchase_order column
            if 'is_purchase_order' not in columns:
                logger.info("Adding 'is_purchase_order' column to orders table")
                connection.execute(text("ALTER TABLE orders ADD COLUMN is_purchase_order BOOLEAN DEFAULT FALSE"))
                logger.info("Added 'is_purchase_order' column")
            
            connection.commit()
            
        logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting database migration")
    migrate_db()
    logger.info("Migration complete") 