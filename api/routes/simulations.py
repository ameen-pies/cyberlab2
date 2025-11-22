from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from api.services.encryption_service import EncryptionService
from api.services.auth_service import AuthService
from api.services.email_service import EmailService
import base64

router = APIRouter(prefix="/simulations", tags=["Security Simulations"])
security = HTTPBearer()

class EncryptRequest(BaseModel):
    data: str
    password: str = None
    recipient_email: Optional[EmailStr] = None

class DecryptRequest(BaseModel):
    encrypted_data: str
    password: str = None
    salt: str = None
    key: str = None

async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token and return user"""
    db = request.state.db
    auth_service = AuthService(db)
    
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    users_collection = db["users"]
    user = await users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# ============= TEXT ENCRYPTION ENDPOINTS =============

@router.post("/encrypt/in-transit")
async def encrypt_in_transit(
    request_data: EncryptRequest,
    request: Request,
    current_user: dict = Depends(verify_token)
):
    """Simulate encryption in transit"""
    if not request_data.password:
        raise HTTPException(status_code=400, detail="Password required for in-transit encryption")
    
    result = EncryptionService.encrypt_in_transit(request_data.data, request_data.password)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    # Send email if recipient provided
    if request_data.recipient_email:
        email_service = EmailService()
        sent = await email_service.send_encrypted_data(
            recipient_email=request_data.recipient_email,
            encrypted_data=result["encrypted_data"],
            salt=result["salt"],
            encryption_type="in-transit",
            sender_email=current_user["email"]
        )
        result["email_sent"] = sent
        result["recipient"] = request_data.recipient_email
    
    return result

@router.post("/decrypt/in-transit")
async def decrypt_in_transit(
    request_data: DecryptRequest,
    request: Request,
    current_user: dict = Depends(verify_token)
):
    """Decrypt data encrypted in transit"""
    if not request_data.password or not request_data.salt:
        raise HTTPException(status_code=400, detail="Password and salt required")
    
    result = EncryptionService.decrypt_in_transit(
        request_data.encrypted_data,
        request_data.password,
        request_data.salt
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.post("/encrypt/at-rest")
async def encrypt_at_rest(
    request_data: EncryptRequest,
    request: Request,
    current_user: dict = Depends(verify_token)
):
    """Simulate encryption at rest"""
    result = EncryptionService.encrypt_at_rest(request_data.data)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    # Send email if recipient provided
    if request_data.recipient_email:
        email_service = EmailService()
        sent = await email_service.send_encrypted_data(
            recipient_email=request_data.recipient_email,
            encrypted_data=result["encrypted_data"],
            key=result["key"],
            encryption_type="at-rest",
            sender_email=current_user["email"]
        )
        result["email_sent"] = sent
        result["recipient"] = request_data.recipient_email
    
    return result

@router.post("/decrypt/at-rest")
async def decrypt_at_rest(
    request_data: DecryptRequest,
    request: Request,
    current_user: dict = Depends(verify_token)
):
    """Decrypt data encrypted at rest"""
    if not request_data.key:
        raise HTTPException(status_code=400, detail="Encryption key required")
    
    result = EncryptionService.decrypt_at_rest(request_data.encrypted_data, request_data.key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.post("/encrypt/lifecycle")
async def encryption_lifecycle(
    request_data: EncryptRequest,
    request: Request,
    current_user: dict = Depends(verify_token)
):
    """Demonstrate complete encryption lifecycle"""
    result = EncryptionService.demonstrate_encryption_lifecycle(request_data.data)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    # Send email if recipient provided
    if request_data.recipient_email:
        email_service = EmailService()
        sent = await email_service.send_encrypted_data(
            recipient_email=request_data.recipient_email,
            encrypted_data=result["stages"]["3_in_transit_encryption"]["encrypted_data"],
            salt=result["stages"]["3_in_transit_encryption"]["salt"],
            encryption_type="full-lifecycle",
            sender_email=current_user["email"],
            additional_info=result["explanation"]
        )
        result["email_sent"] = sent
        result["recipient"] = request_data.recipient_email
    
    return result

# ============= FILE ENCRYPTION ENDPOINTS =============

@router.post("/encrypt/file/in-transit")
async def encrypt_file_in_transit(
    request: Request,
    file: UploadFile = File(...),
    password: str = Form(...),
    recipient_email: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Encrypt uploaded file for transit"""
    current_user = await verify_token(request, credentials)
    
    # Read file content
    file_content = await file.read()
    file_b64 = base64.b64encode(file_content).decode()
    
    # Encrypt the base64 encoded file
    result = EncryptionService.encrypt_in_transit(file_b64, password)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    result["original_filename"] = file.filename
    result["file_size"] = len(file_content)
    result["content_type"] = file.content_type
    
    # Send email if recipient provided
    if recipient_email:
        email_service = EmailService()
        sent = await email_service.send_encrypted_file(
            recipient_email=recipient_email,
            encrypted_data=result["encrypted_data"],
            salt=result["salt"],
            filename=file.filename,
            encryption_type="in-transit",
            sender_email=current_user["email"]
        )
        result["email_sent"] = sent
        result["recipient"] = recipient_email
    
    return result

@router.post("/encrypt/file/at-rest")
async def encrypt_file_at_rest(
    request: Request,
    file: UploadFile = File(...),
    recipient_email: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Encrypt uploaded file for storage at rest"""
    current_user = await verify_token(request, credentials)
    
    # Read file content
    file_content = await file.read()
    file_b64 = base64.b64encode(file_content).decode()
    
    # Encrypt the base64 encoded file
    result = EncryptionService.encrypt_at_rest(file_b64)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    result["original_filename"] = file.filename
    result["file_size"] = len(file_content)
    result["content_type"] = file.content_type
    
    # Send email if recipient provided
    if recipient_email:
        email_service = EmailService()
        sent = await email_service.send_encrypted_file(
            recipient_email=recipient_email,
            encrypted_data=result["encrypted_data"],
            key=result["key"],
            filename=file.filename,
            encryption_type="at-rest",
            sender_email=current_user["email"]
        )
        result["email_sent"] = sent
        result["recipient"] = recipient_email
    
    return result

@router.post("/encrypt/file/lifecycle")
async def encrypt_file_lifecycle(
    request: Request,
    file: UploadFile = File(...),
    recipient_email: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Demonstrate complete file encryption lifecycle"""
    current_user = await verify_token(request, credentials)
    
    # Read file content
    file_content = await file.read()
    file_b64 = base64.b64encode(file_content).decode()
    
    # Full lifecycle
    result = EncryptionService.demonstrate_encryption_lifecycle(file_b64)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    result["original_filename"] = file.filename
    result["file_size"] = len(file_content)
    result["content_type"] = file.content_type
    
    # Send email if recipient provided
    if recipient_email:
        email_service = EmailService()
        sent = await email_service.send_encrypted_file(
            recipient_email=recipient_email,
            encrypted_data=result["stages"]["3_in_transit_encryption"]["encrypted_data"],
            salt=result["stages"]["3_in_transit_encryption"]["salt"],
            filename=file.filename,
            encryption_type="full-lifecycle",
            sender_email=current_user["email"],
            additional_info=result["explanation"]
        )
        result["email_sent"] = sent
        result["recipient"] = recipient_email
    
    return result