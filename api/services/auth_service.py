from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from shared.config.settings import settings
from api.utils.crypto import hash_password, verify_password
from api.models.user import User, UserRole, Permission
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.users_collection = db["users"]
        self.mfa_codes_collection = db["mfa_codes"]
        
        # DEBUG: Log initialization
        logger.info(f"🔧 AuthService initialized")
        logger.info(f"🔧 Database name: {db.name}")
        logger.info(f"🔧 Users collection: users")
    
    async def create_user(
        self, 
        email: str, 
        password: str, 
        full_name: str,
        role: UserRole = UserRole.NORMAL,
        custom_permissions: List[Permission] = [],
        created_by: Optional[str] = None
    ) -> Optional[dict]:
        """Create a new user with RBAC"""
        try:
            logger.info(f"📝 Creating user: {email}")
            
            existing_user = await self.users_collection.find_one({"email": email})
            if existing_user:
                logger.warning(f"❌ User creation failed - email already exists: {email}")
                return None
            
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                is_verified=True,
                mfa_enabled=True,
                role=role,
                custom_permissions=custom_permissions,
                created_by=created_by
            )
            
            result = await self.users_collection.insert_one(user.model_dump())
            user_dict = user.model_dump()
            user_dict["_id"] = str(result.inserted_id)
            
            logger.info(f"✅ User created: {email} with role {role.value}")
            return user_dict
            
        except Exception as e:
            logger.error(f"❌ Error creating user: {str(e)}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password"""
        try:
            logger.info(f"="*60)
            logger.info(f"🔍 AUTH ATTEMPT")
            logger.info(f"="*60)
            logger.info(f"📧 Email: {email}")
            logger.info(f"🔐 Password length: {len(password)}")
            logger.info(f"🗄️  Database: {self.db.name}")
            logger.info(f"📋 Collection: {self.users_collection.name}")
            
            # Try to find user
            logger.info(f"🔍 Searching for user in database...")
            user = await self.users_collection.find_one({"email": email})
            
            if not user:
                logger.warning(f"❌ USER NOT FOUND: {email}")
                logger.warning(f"🔍 Let me check what users exist:")
                
                # DEBUG: Show all users in collection
                all_users = await self.users_collection.find({}).to_list(length=10)
                logger.warning(f"📋 Total users in collection: {len(all_users)}")
                for u in all_users:
                    logger.warning(f"   - {u.get('email', 'NO EMAIL')}")
                
                return None
            
            logger.info(f"✅ USER FOUND: {email}")
            logger.info(f"👤 Full name: {user.get('full_name')}")
            logger.info(f"🎭 Role: {user.get('role')}")
            logger.info(f"✔️  Active: {user.get('is_active')}")
            logger.info(f"✔️  Verified: {user.get('is_verified')}")
            logger.info(f"🔐 Has password hash: {bool(user.get('hashed_password'))}")
            
            # Check if active
            if not user.get("is_active", True):
                logger.warning(f"❌ USER DEACTIVATED: {email}")
                return None
            
            logger.info(f"🔍 Verifying password...")
            stored_hash = user.get("hashed_password")
            logger.info(f"🔐 Stored hash (first 30 chars): {stored_hash[:30]}...")
            
            password_valid = verify_password(password, stored_hash)
            logger.info(f"🔐 Password verification result: {password_valid}")
            
            if not password_valid:
                logger.warning(f"❌ INVALID PASSWORD for: {email}")
                return None
            
            # Update last login
            await self.users_collection.update_one(
                {"email": email},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            logger.info(f"✅✅✅ AUTHENTICATION SUCCESSFUL: {email}")
            logger.info(f"="*60)
            return user
            
        except Exception as e:
            logger.error(f"❌❌❌ AUTHENTICATION ERROR: {str(e)}")
            logger.exception(e)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        try:
            user = await self.users_collection.find_one({"email": email})
            if user:
                user["_id"] = str(user["_id"])
                user.pop("hashed_password", None)
                user.pop("mfa_secret", None)
            return user
        except Exception as e:
            logger.error(f"❌ Error fetching user: {str(e)}")
            return None
    
    async def store_mfa_code(self, email: str, code: str) -> bool:
        """Store MFA code with expiration"""
        try:
            logger.info(f"📧 Storing MFA code for: {email}")
            
            user = await self.users_collection.find_one({"email": email})
            if not user:
                logger.error(f"❌ Cannot store MFA code - user not found: {email}")
                return False
            
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
            
            logger.info(f"✅ MFA code stored for {email} (expires in {settings.MFA_CODE_EXPIRY}s)")
            logger.info(f"🔢 MFA Code: {code}")  # REMOVE IN PRODUCTION!
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing MFA code: {str(e)}")
            return False
    
    async def verify_mfa_code(self, email: str, code: str) -> bool:
        """Verify MFA code"""
        try:
            logger.info(f"🔍 Verifying MFA code for: {email}")
            logger.info(f"🔢 Code provided: {code}")
            
            mfa_record = await self.mfa_codes_collection.find_one({"email": email})
            
            if not mfa_record:
                logger.warning(f"❌ MFA verification failed - no code found for: {email}")
                return False
            
            logger.info(f"🔢 Stored code: {mfa_record.get('code')}")
            logger.info(f"⏰ Expiry: {mfa_record.get('expiry')}")
            logger.info(f"⏰ Now: {datetime.utcnow()}")
            
            if datetime.utcnow() > mfa_record["expiry"]:
                logger.warning(f"❌ MFA verification failed - code expired for: {email}")
                await self.mfa_codes_collection.delete_one({"email": email})
                return False
            
            if mfa_record["code"] != code:
                logger.warning(f"❌ MFA verification failed - invalid code for: {email}")
                return False
            
            await self.mfa_codes_collection.delete_one({"email": email})
            logger.info(f"✅ MFA code verified successfully for: {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying MFA code: {str(e)}")
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
        
        logger.info(f"🎫 Access token created for: {data.get('sub')}")
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"❌ Token decode failed: {str(e)}")
            return None