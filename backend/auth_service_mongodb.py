"""
MongoDB Authentication Service
==============================

Handles user authentication with MongoDB instead of SQLAlchemy.

Key Changes from SQLite:
- Uses Motor (async MongoDB driver)
- All operations are async
- Uses MongoDB queries instead of SQLAlchemy ORM
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import secrets
from mongodb_models import UserModel, UserSubscriptionModel, SubscriptionTier, SubscriptionStatus

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class MongoDBAuthService:
    """Authentication service using MongoDB"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.subscriptions_collection = db.user_subscriptions
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        requirements = {
            "min_length": len(password) >= 8,
            "has_uppercase": any(c.isupper() for c in password),
            "has_lowercase": any(c.islower() for c in password),
            "has_digit": any(c.isdigit() for c in password),
        }
        
        score = sum(requirements.values())
        strength = "strong" if score >= 4 else "weak" if score >= 2 else "very_weak"
        
        return {
            "strength": strength,
            "score": score,
            "max_score": len(requirements),
            "requirements": requirements
        }
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get user by email address
        
        Args:
            email: User email
        
        Returns:
            UserModel if found, None otherwise
        """
        user_data = await self.users_collection.find_one({"email": email})
        if user_data:
            return UserModel(**user_data)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
        
        Returns:
            UserModel if found, None otherwise
        """
        user_data = await self.users_collection.find_one({"id": user_id})
        if user_data:
            return UserModel(**user_data)
        return None
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str
    ) -> UserModel:
        """
        Create a new user account
        
        Args:
            email: User email
            password: Plain text password
            full_name: User's full name
        
        Returns:
            Created UserModel
        
        Raises:
            HTTPException: If user already exists
        """
        # Check if user exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Validate password strength
        strength_check = self.validate_password_strength(password)
        if strength_check["strength"] == "very_weak":
            raise HTTPException(
                status_code=400,
                detail="Password is too weak. Please include uppercase, lowercase, and numbers."
            )
        
        # Create user
        user = UserModel(
            email=email,
            full_name=full_name,
            hashed_password=self.get_password_hash(password),
            is_active=True
        )
        
        # Insert into database
        await self.users_collection.insert_one(user.model_dump())
        
        # Create default free subscription
        subscription = UserSubscriptionModel(
            user_id=user.id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE
        )
        
        await self.subscriptions_collection.insert_one(subscription.model_dump())
        
        return user
    
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[UserModel]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: Plain text password
        
        Returns:
            UserModel if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        await self.users_collection.update_one(
            {"id": user.id},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        return user
    
    async def get_user_subscription(self, user_id: str) -> Optional[UserSubscriptionModel]:
        """
        Get user's subscription details
        
        Args:
            user_id: User ID
        
        Returns:
            UserSubscriptionModel if found, None otherwise
        """
        sub_data = await self.subscriptions_collection.find_one({"user_id": user_id})
        if sub_data:
            return UserSubscriptionModel(**sub_data)
        return None
    
    async def update_quick_scan_counter(self, user_id: str) -> bool:
        """
        Increment quick scan counter for rate limiting
        
        Resets counter if it's a new day
        
        Args:
            user_id: User ID
        
        Returns:
            True if updated successfully
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check if we need to reset counter
        if user.quick_scans_reset_date < today:
            # New day, reset counter
            await self.users_collection.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "quick_scans_today": 1,
                        "quick_scans_reset_date": now
                    }
                }
            )
        else:
            # Same day, increment
            await self.users_collection.update_one(
                {"id": user_id},
                {
                    "$inc": {"quick_scans_today": 1}
                }
            )
        
        return True
