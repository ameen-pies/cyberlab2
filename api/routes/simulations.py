from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.services.encryption_service import EncryptionService
from api.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/simulations", tags=["Security Simulations"])

class EncryptRequest(BaseModel):
    data: str
    password: str = None

class DecryptRequest(BaseModel):
    encrypted_data: str
    password: str = None
    salt: str = None
    key: str = None

@router.post("/encrypt/in-transit")
async def encrypt_in_transit(
    request: EncryptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Simulate encryption in transit"""
    if not request.password:
        raise HTTPException(status_code=400, detail="Password required for in-transit encryption")
    
    result = EncryptionService.encrypt_in_transit(request.data, request.password)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.post("/decrypt/in-transit")
async def decrypt_in_transit(
    request: DecryptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Decrypt data encrypted in transit"""
    if not request.password or not request.salt:
        raise HTTPException(status_code=400, detail="Password and salt required")
    
    result = EncryptionService.decrypt_in_transit(
        request.encrypted_data,
        request.password,
        request.salt
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.post("/encrypt/at-rest")
async def encrypt_at_rest(
    request: EncryptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Simulate encryption at rest"""
    result = EncryptionService.encrypt_at_rest(request.data)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.post("/decrypt/at-rest")
async def decrypt_at_rest(
    request: DecryptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Decrypt data encrypted at rest"""
    if not request.key:
        raise HTTPException(status_code=400, detail="Encryption key required")
    
    result = EncryptionService.decrypt_at_rest(request.encrypted_data, request.key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.post("/encrypt/lifecycle")
async def encryption_lifecycle(
    request: EncryptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Demonstrate complete encryption lifecycle"""
    result = EncryptionService.demonstrate_encryption_lifecycle(request.data)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result