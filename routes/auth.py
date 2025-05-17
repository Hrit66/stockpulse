from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import User
from ..schemas import UserCreate, UserLogin, PasswordChange
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import logging
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-here"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Return user as a dictionary instead of an ORM object
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
    }

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user:
            logger.warning(f"Login attempt failed: User {form_data.username} not found")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not pwd_context.verify(form_data.password, user.hashed_password):
            logger.warning(f"Login attempt failed: Invalid password for user {form_data.username}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        access_token = create_access_token(data={"sub": user.username, "is_admin": user.is_admin})
        logger.info(f"User {user.username} logged in successfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "is_admin": user.is_admin,
            "username": user.username
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Create new user with is_admin set to False
        hashed_password = pwd_context.hash(user_data.password)
        db_user = User(username=user_data.username, hashed_password=hashed_password, is_admin=False)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"New user registered: {user_data.username}")
        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/create-admin")
def create_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Create new admin user
        hashed_password = pwd_context.hash(user_data.password)
        db_user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            is_admin=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"New admin user created: {user_data.username}")
        return {"message": "Admin user created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange, 
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        # Get user from database
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            logger.warning(f"Password change failed: User {current_user['username']} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not pwd_context.verify(password_data.current_password, user.hashed_password):
            logger.warning(f"Password change failed: Incorrect current password for {current_user['username']}")
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        user.hashed_password = pwd_context.hash(password_data.new_password)
        db.commit()
        
        logger.info(f"Password changed successfully for user {current_user['username']}")
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password") 