from database import SessionLocal
from models import User
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_admin_user():
    db = SessionLocal()
    try:
        logger.info("Checking for admin user...")
        admin = db.query(User).filter(User.username == "admin@stockpulse.com").first()
        if admin:
            logger.info("Admin user exists:")
            logger.info(f"Username: {admin.username}")
            logger.info(f"Is Admin: {admin.is_admin}")
        else:
            logger.warning("Admin user not found")
            
        # List all users
        all_users = db.query(User).all()
        logger.info(f"Total users in database: {len(all_users)}")
        for user in all_users:
            logger.info(f"User: {user.username}, Is Admin: {user.is_admin}")
            
    except Exception as e:
        logger.error(f"Error checking admin user: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        check_admin_user()
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1) 