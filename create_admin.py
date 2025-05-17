import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend2.database import SessionLocal
from backend2.models import User
from passlib.context import CryptContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user():
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.username == "admin@stockpulse.com").first()
        if admin:
            logger.info("Admin user already exists")
            return

        # Create admin user
        hashed_password = pwd_context.hash("admin123")
        admin_user = User(
            username="admin@stockpulse.com",
            hashed_password=hashed_password,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        logger.info("Admin user created successfully")
        logger.info("Username: admin@stockpulse.com")
        logger.info("Password: admin123")
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 