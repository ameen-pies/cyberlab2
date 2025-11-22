from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from api.middleware.rbac_middleware import get_current_user, require_permission
from api.services.keyvault_service import KeyVaultService
from api.models.user import Permission
import logging
import base64
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration from .env
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/keyvault", tags=["KeyVault Management"])

# ============== Request Models ==============

class KeyGenerateRequest(BaseModel):
    key_name: str
    key_type: str = "RSA"
    key_size: int = 2048
    metadata: Optional[Dict] = None

class CertificateGenerateRequest(BaseModel):
    cert_name: str
    common_name: str
    validity_days: int = 365
    metadata: Optional[Dict] = None

class SendKeyEmailRequest(BaseModel):
    recipient_email: EmailStr
    include_private_key: bool = False
    message: Optional[str] = None

class SendCertEmailRequest(BaseModel):
    recipient_email: EmailStr
    include_private_key: bool = False
    message: Optional[str] = None

# ============== Helper Functions ==============

def check_permission(current_user: dict, required_permission: str):
    """Check if user has a specific permission"""
    user_role = current_user.get('role', '')
    user_perms = current_user.get('permissions', [])
    
    # Admin bypass - admins have all permissions
    if user_role == 'admin':
        logger.info(f"✅ Admin user {current_user['email']} - permission granted")
        return True
    
    # Check specific permission
    if required_permission in user_perms:
        return True
    
    logger.warning(f"❌ User {current_user['email']} lacks permission: {required_permission}")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"You don't have permission: {required_permission}"
    )

def check_any_permission(current_user: dict, permissions: list):
    """Check if user has any of the specified permissions"""
    user_role = current_user.get('role', '')
    user_perms = current_user.get('permissions', [])
    
    if user_role == 'admin':
        return True
    
    for perm in permissions:
        if perm in user_perms:
            return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"You need one of these permissions: {', '.join(permissions)}"
    )

async def send_key_email(
    recipient: str,
    subject: str,
    body: str,
    attachments: List[Dict[str, str]]
) -> bool:
    """Send email with key/certificate attachments"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Add attachments
        for att in attachments:
            part = MIMEApplication(att['content'].encode(), Name=att['filename'])
            part['Content-Disposition'] = f'attachment; filename="{att["filename"]}"'
            msg.attach(part)
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email sent to {recipient}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email: {str(e)}")
        return False

# ============== Key Endpoints ==============

@router.post("/keys/generate")
async def generate_key(
    request_data: KeyGenerateRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Generate a new cryptographic key (RSA or AES)"""
    check_permission(current_user, "keyvault_generate_keys")
    
    logger.info(f"🔑 Key generation request from {current_user['email']}")
    
    db = req.state.db
    
    key = await KeyVaultService.generate_key(
        db=db,
        user_email=current_user['email'],
        key_name=request_data.key_name,
        key_type=request_data.key_type,
        key_size=request_data.key_size,
        metadata=request_data.metadata
    )
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Key name '{request_data.key_name}' already exists"
        )
    
    return {
        "success": True,
        "message": f"Key '{request_data.key_name}' generated successfully",
        "key": key
    }

@router.get("/keys")
async def list_keys(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """List all keys for current user"""
    db = req.state.db
    keys = await KeyVaultService.list_keys(db, current_user['email'])
    
    return {
        "success": True,
        "keys": keys,
        "total": len(keys)
    }

@router.get("/keys/{key_id}")
async def get_key(
    key_id: str,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get key information (metadata only, not private material)"""
    db = req.state.db
    key = await KeyVaultService.get_key(db, current_user['email'], key_id)
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found"
        )
    
    return {"success": True, "key": key}

@router.post("/keys/{key_id}/rotate")
async def rotate_key(
    key_id: str,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Rotate a key (create new version)"""
    check_keyvault_permission(current_user)
    
    logger.info(f"🔄 Key rotation request for {key_id} by {current_user['email']}")
    
    db = req.state.db
    result = await KeyVaultService.rotate_key(db, current_user['email'], key_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found or rotation failed"
        )
    
    return {
        "success": True,
        "message": "Key rotated successfully",
        "rotation": result
    }

@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: str,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete a key (soft delete)"""
    check_keyvault_permission(current_user)
    
    db = req.state.db
    deleted = await KeyVaultService.delete_key(db, current_user['email'], key_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found"
        )
    
    return {"success": True, "message": "Key deleted successfully"}

@router.get("/keys/{key_id}/download")
async def download_key(
    key_id: str,
    include_private: bool = False,
    req: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Download key as PEM file"""
    check_keyvault_permission(current_user)
    
    db = req.state.db
    keys_collection = db["keys"]
    
    key = await keys_collection.find_one({
        "key_id": key_id,
        "user_email": current_user['email'],
        "is_deleted": False
    })
    
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_name = key["key_name"]
    key_type = key["key_type"]
    
    if key_type == "RSA":
        if include_private:
            content = base64.b64decode(key["key_material"]["private_key"]).decode()
            filename = f"{key_name}_private.pem"
        else:
            content = base64.b64decode(key["key_material"]["public_key"]).decode()
            filename = f"{key_name}_public.pem"
    elif key_type == "AES":
        if not include_private:
            raise HTTPException(
                status_code=400,
                detail="AES keys only have private material. Set include_private=true"
            )
        content = base64.b64decode(key["key_material"]["key"]).decode('latin-1')
        filename = f"{key_name}_aes.key"
    else:
        raise HTTPException(status_code=400, detail="Unknown key type")
    
    logger.info(f"📥 Key download: {key_id} by {current_user['email']}")
    
    return Response(
        content=content,
        media_type="application/x-pem-file",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/keys/{key_id}/send-email")
async def send_key_via_email(
    key_id: str,
    request_data: SendKeyEmailRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Send key via email"""
    check_keyvault_permission(current_user)
    
    db = req.state.db
    keys_collection = db["keys"]
    
    key = await keys_collection.find_one({
        "key_id": key_id,
        "user_email": current_user['email'],
        "is_deleted": False
    })
    
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_name = key["key_name"]
    key_type = key["key_type"]
    attachments = []
    
    # Prepare attachments
    if key_type == "RSA":
        public_key = base64.b64decode(key["key_material"]["public_key"]).decode()
        attachments.append({
            "filename": f"{key_name}_public.pem",
            "content": public_key
        })
        
        if request_data.include_private_key:
            private_key = base64.b64decode(key["key_material"]["private_key"]).decode()
            attachments.append({
                "filename": f"{key_name}_private.pem",
                "content": private_key
            })
    
    elif key_type == "AES":
        if request_data.include_private_key:
            aes_key = base64.b64decode(key["key_material"]["key"]).decode('latin-1')
            attachments.append({
                "filename": f"{key_name}_aes.key",
                "content": aes_key
            })
        else:
            raise HTTPException(
                status_code=400,
                detail="AES keys only have private material"
            )
    
    # Prepare email
    custom_msg = request_data.message or ""
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>🔑 Cryptographic Key Shared</h2>
        <p>A cryptographic key has been shared with you from CyberLab Platform.</p>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Key Name:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{key_name}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Key Type:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{key_type}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Key Size:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{key["key_size"]} bits</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Sent By:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{current_user['email']}</td></tr>
        </table>
        {f'<p><strong>Message:</strong> {custom_msg}</p>' if custom_msg else ''}
        <p style="color: #dc2626; font-weight: bold;">
            ⚠️ Keep private keys secure and never share them over insecure channels!
        </p>
        <hr>
        <p style="color: #6b7280; font-size: 12px;">CyberLab Security Platform</p>
    </body>
    </html>
    """
    
    success = await send_key_email(
        recipient=request_data.recipient_email,
        subject=f"🔑 Cryptographic Key: {key_name}",
        body=body,
        attachments=attachments
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    logger.info(f"📧 Key {key_id} sent to {request_data.recipient_email} by {current_user['email']}")
    
    return {
        "success": True,
        "message": f"Key sent to {request_data.recipient_email}",
        "included_private_key": request_data.include_private_key
    }

# ============== Certificate Endpoints ==============

@router.post("/certificates/generate")
async def generate_certificate(
    request_data: CertificateGenerateRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Generate a self-signed certificate"""
    check_keyvault_permission(current_user)
    
    logger.info(f"📜 Certificate generation request from {current_user['email']}")
    
    db = req.state.db
    
    cert = await KeyVaultService.generate_certificate(
        db=db,
        user_email=current_user['email'],
        cert_name=request_data.cert_name,
        common_name=request_data.common_name,
        validity_days=request_data.validity_days,
        metadata=request_data.metadata
    )
    
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate name '{request_data.cert_name}' already exists"
        )
    
    return {
        "success": True,
        "message": f"Certificate '{request_data.cert_name}' generated successfully",
        "certificate": cert
    }

@router.get("/certificates")
async def list_certificates(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """List all certificates for current user"""
    db = req.state.db
    certs_collection = db["certificates"]
    
    certs = await certs_collection.find({
        "user_email": current_user['email'],
        "is_deleted": False
    }).to_list(length=None)
    
    for cert in certs:
        cert["_id"] = str(cert["_id"])
        cert.pop("private_key", None)
    
    return {
        "success": True,
        "certificates": certs,
        "total": len(certs)
    }

@router.post("/certificates/{cert_id}/validate")
async def validate_certificate(
    cert_id: str,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Validate certificate and check expiration"""
    db = req.state.db
    
    validation = await KeyVaultService.validate_certificate(
        db, current_user['email'], cert_id
    )
    
    return {"success": True, "validation": validation}

@router.get("/certificates/{cert_id}/download")
async def download_certificate(
    cert_id: str,
    include_private_key: bool = False,
    req: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Download certificate as PEM file"""
    check_keyvault_permission(current_user)
    
    db = req.state.db
    certs_collection = db["certificates"]
    
    cert = await certs_collection.find_one({
        "cert_id": cert_id,
        "user_email": current_user['email'],
        "is_deleted": False
    })
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    cert_name = cert["cert_name"]
    
    if include_private_key:
        # Return both cert and private key in one file
        cert_pem = base64.b64decode(cert["certificate"]).decode()
        key_pem = base64.b64decode(cert["private_key"]).decode()
        content = f"{cert_pem}\n{key_pem}"
        filename = f"{cert_name}_bundle.pem"
    else:
        content = base64.b64decode(cert["certificate"]).decode()
        filename = f"{cert_name}.pem"
    
    logger.info(f"📥 Certificate download: {cert_id} by {current_user['email']}")
    
    return Response(
        content=content,
        media_type="application/x-pem-file",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/certificates/{cert_id}/send-email")
async def send_certificate_via_email(
    cert_id: str,
    request_data: SendCertEmailRequest,
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Send certificate via email"""
    check_keyvault_permission(current_user)
    
    db = req.state.db
    certs_collection = db["certificates"]
    
    cert = await certs_collection.find_one({
        "cert_id": cert_id,
        "user_email": current_user['email'],
        "is_deleted": False
    })
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    cert_name = cert["cert_name"]
    attachments = []
    
    # Certificate attachment
    cert_pem = base64.b64decode(cert["certificate"]).decode()
    attachments.append({
        "filename": f"{cert_name}.pem",
        "content": cert_pem
    })
    
    # Private key attachment (optional)
    if request_data.include_private_key:
        key_pem = base64.b64decode(cert["private_key"]).decode()
        attachments.append({
            "filename": f"{cert_name}_private.key",
            "content": key_pem
        })
    
    custom_msg = request_data.message or ""
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>📜 Certificate Shared</h2>
        <p>A certificate has been shared with you from CyberLab Platform.</p>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Certificate Name:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{cert_name}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Common Name:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{cert["common_name"]}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Valid Until:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{cert["not_after"]}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Sent By:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{current_user['email']}</td></tr>
        </table>
        {f'<p><strong>Message:</strong> {custom_msg}</p>' if custom_msg else ''}
        <p style="color: #dc2626; font-weight: bold;">
            ⚠️ Keep private keys secure and never share them over insecure channels!
        </p>
        <hr>
        <p style="color: #6b7280; font-size: 12px;">CyberLab Security Platform</p>
    </body>
    </html>
    """
    
    success = await send_key_email(
        recipient=request_data.recipient_email,
        subject=f"📜 Certificate: {cert_name}",
        body=body,
        attachments=attachments
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    logger.info(f"📧 Certificate {cert_id} sent to {request_data.recipient_email}")
    
    return {
        "success": True,
        "message": f"Certificate sent to {request_data.recipient_email}",
        "included_private_key": request_data.include_private_key
    }

# ============== Statistics ==============

@router.get("/statistics")
async def get_vault_statistics(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get KeyVault usage statistics for current user"""
    db = req.state.db
    
    keys_collection = db["keys"]
    total_keys = await keys_collection.count_documents({
        "user_email": current_user['email'],
        "is_deleted": False
    })
    
    certs_collection = db["certificates"]
    total_certs = await certs_collection.count_documents({
        "user_email": current_user['email'],
        "is_deleted": False
    })
    
    from datetime import datetime, timedelta
    expiring_soon = await certs_collection.count_documents({
        "user_email": current_user['email'],
        "is_deleted": False,
        "not_after": {"$lte": datetime.utcnow() + timedelta(days=30)}
    })
    
    return {
        "success": True,
        "statistics": {
            "total_keys": total_keys,
            "total_certificates": total_certs,
            "expiring_certificates": expiring_soon
        }
    }