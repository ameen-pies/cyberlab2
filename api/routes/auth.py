from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from shared.schemas.user import UserCreate, UserLogin, Token
from shared.schemas.mfa import MFARequest, MFAVerify, MFAResponse
from api.services.auth_service import AuthService
from api.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncIOMotorClient = Depends()):
    """Register a new user"""
    auth_service = AuthService(db)
    
    user = await auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    return {
        "success": True,
        "message": "User registered successfully",
        "email": user["email"]
    }

@router.post("/login")
async def login(credentials: UserLogin, db: AsyncIOMotorClient = Depends()):
    """Initial login - returns success, requires MFA"""
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    return {
        "success": True,
        "message": "Credentials verified. Please complete MFA.",
        "mfa_required": True,
        "email": user["email"]
    }

@router.post("/mfa/send")
async def send_mfa_code(request: MFARequest, db: AsyncIOMotorClient = Depends()):
    """Send MFA code to user's email"""
    auth_service = AuthService(db)
    email_service = EmailService()
    
    code = email_service.generate_mfa_code()
    
    stored = await auth_service.store_mfa_code(request.email, code)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate MFA code"
        )
    
    sent = await email_service.send_mfa_code(request.email, code)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send MFA code"
        )
    
    return {
        "success": True,
        "message": f"MFA code sent to {request.email}"
    }

@router.post("/mfa/verify", response_model=Token)
async def verify_mfa_code(request: MFAVerify, db: AsyncIOMotorClient = Depends()):
    """Verify MFA code and return JWT token"""
    auth_service = AuthService(db)
    
    verified = await auth_service.verify_mfa_code(request.email, request.code)
    
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA code"
        )
    
    access_token = auth_service.create_access_token(data={"sub": request.email})
    
    return Token(access_token=access_token)

@router.get("/me")
async def get_current_user_info(db: AsyncIOMotorClient = Depends()):
    """Get current user information (protected route example)"""
    return {
        "message": "This is a protected route",
        "user": "Current user info would go here"
    }