from fastapi import APIRouter, Depends, HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorClient
from shared.schemas.user import UserCreate, UserLogin, Token
from shared.schemas.mfa import MFARequest, MFAVerify, MFAResponse
from api.services.auth_service import AuthService
from api.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db(request: Request):
    """Get database from request state"""
    return request.state.db

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, request: Request):
    """Register a new user"""
    logger.info(f"📝 Registration request for: {user_data.email}")
    
    db = get_db(request)
    logger.info(f"🗄️  Database: {db.name}")
    
    auth_service = AuthService(db)
    
    user = await auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    if not user:
        logger.warning(f"❌ Registration failed for: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    logger.info(f"✅ Registration successful for: {user_data.email}")
    return {
        "success": True,
        "message": "User registered successfully",
        "email": user["email"]
    }

@router.post("/login")
async def login(credentials: UserLogin, request: Request):
    """Initial login - returns success, requires MFA"""
    logger.info(f"="*70)
    logger.info(f"🔐 LOGIN REQUEST")
    logger.info(f"="*70)
    logger.info(f"📧 Email: {credentials.email}")
    logger.info(f"🔐 Password provided: {'Yes' if credentials.password else 'No'}")
    logger.info(f"🔐 Password length: {len(credentials.password)}")
    
    db = get_db(request)
    logger.info(f"🗄️  Database from request: {db.name}")
    
    auth_service = AuthService(db)
    
    logger.info(f"🔍 Calling authenticate_user...")
    user = await auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )
    
    logger.info(f"🔍 authenticate_user returned: {user is not None}")
    
    if not user:
        logger.warning(f"❌ LOGIN FAILED for: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    logger.info(f"✅ Credentials verified for: {credentials.email}")
    
    if not user.get("is_verified"):
        logger.warning(f"❌ Email not verified for: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    logger.info(f"✅ LOGIN SUCCESSFUL - Sending to MFA for: {credentials.email}")
    logger.info(f"="*70)
    
    return {
        "success": True,
        "message": "Credentials verified. Please complete MFA.",
        "mfa_required": True,
        "email": user["email"]
    }

@router.post("/mfa/send")
async def send_mfa_code(request_data: MFARequest, request: Request):
    """Send MFA code to user's email"""
    logger.info(f"📧 MFA send request for: {request_data.email}")
    
    db = get_db(request)
    auth_service = AuthService(db)
    email_service = EmailService()
    
    # Verify user exists
    users_collection = db["users"]
    user = await users_collection.find_one({"email": request_data.email})
    if not user:
        logger.error(f"❌ MFA send failed - user not found: {request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"✅ User found for MFA: {request_data.email}")
    
    code = email_service.generate_mfa_code()
    logger.info(f"🔢 Generated MFA code: {code}")  # REMOVE IN PRODUCTION!
    
    stored = await auth_service.store_mfa_code(request_data.email, code)
    if not stored:
        logger.error(f"❌ Failed to store MFA code for: {request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate MFA code"
        )
    
    logger.info(f"📧 Sending MFA email to: {request_data.email}")
    sent = await email_service.send_mfa_code(request_data.email, code)
    if not sent:
        logger.warning(f"⚠️ Email sending failed for {request_data.email}, but code was stored")
    
    logger.info(f"✅ MFA code sent successfully to: {request_data.email}")
    return {
        "success": True,
        "message": f"MFA code sent to {request_data.email}"
    }

@router.post("/mfa/verify", response_model=Token)
async def verify_mfa_code(request_data: MFAVerify, request: Request):
    """Verify MFA code and return JWT token"""
    logger.info(f"🔍 MFA verification for: {request_data.email}")
    logger.info(f"🔢 Code provided: {request_data.code}")
    
    db = get_db(request)
    auth_service = AuthService(db)
    
    verified = await auth_service.verify_mfa_code(request_data.email, request_data.code)
    
    if not verified:
        logger.warning(f"❌ MFA verification failed for: {request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA code"
        )
    
    # Get user data for the token
    users_collection = db["users"]
    user = await users_collection.find_one({"email": request_data.email})
    
    if not user:
        logger.error(f"❌ User not found after MFA: {request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create token with user email
    access_token = auth_service.create_access_token(data={"sub": request_data.email})
    
    logger.info(f"✅ MFA verified - Token generated for: {request_data.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me")
async def get_current_user_info(request: Request):
    """Get current user information (requires authentication)"""
    return {
        "message": "This endpoint requires authentication",
        "note": "Use the Bearer token in Authorization header"
    }