from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from shared.config.settings import settings
from api.utils.crypto import hash_password, verify_password
from api.models.user import User
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.users_collection = db[settings.DATABASE_NAME]["users"]
        self.mfa_codes_collection = db[settings.DATABASE_NAME]["mfa_codes"]
    
    async def create_user(self, email: str, password: str, full_name: str) -> Optional[dict]:
        """Create a new user"""
        try:
            existing_user = await self.users_collection.find_one({"email": email})
            if existing_user:
                return None
            
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                is_verified=True,  # Auto-verify for demo purposes
                mfa_enabled=True
            )
            
            result = await self.users_collection.insert_one(user.model_dump())
            user_dict = user.model_dump()
            user_dict["_id"] = str(result.inserted_id)
            
            logger.info(f"User created successfully: {email}")
            return user_dict
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password"""
        try:
            user = await self.users_collection.find_one({"email": email})
            if not user:
                return None
            
            if not verify_password(password, user["hashed_password"]):
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    async def store_mfa_code(self, email: str, code: str) -> bool:
        """Store MFA code with expiration"""
        try:
            expiry = datetime.utcnow() + timedelta(seconds=settings.MFA_CODE_EXPIRY)
            
            await self.mfa_codes_collection.update_one(
                {"email": email},
                {
                    "$set": {
                        "code": code,
                        "expiry": expiry,
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"MFA code stored for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing MFA code: {str(e)}")
            return False
    
    async def verify_mfa_code(self, email: str, code: str) -> bool:
        """Verify MFA code"""
        try:
            mfa_record = await self.mfa_codes_collection.find_one({"email": email})
            
            if not mfa_record:
                return False
            
            if datetime.utcnow() > mfa_record["expiry"]:
                await self.mfa_codes_collection.delete_one({"email": email})
                return False
            
            if mfa_record["code"] != code:
                return False
            
            await self.mfa_codes_collection.delete_one({"email": email})
            logger.info(f"MFA code verified for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying MFA code: {str(e)}")
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None