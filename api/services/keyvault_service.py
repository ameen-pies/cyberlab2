from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import secrets
import base64
import logging

logger = logging.getLogger(__name__)

class KeyVaultService:
    """
    Manages cryptographic keys and certificates
    Simulates AWS KMS / Azure KeyVault functionality
    """
    
    @staticmethod
    async def generate_key(
        db,
        user_email: str,
        key_name: str,
        key_type: str = "RSA",
        key_size: int = 2048,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Generate and store a cryptographic key"""
        try:
            logger.info(f"🔑 Generating {key_type} key '{key_name}' for {user_email}")
            
            keys_collection = db["keys"]
            
            # Check if key name already exists for this user
            existing = await keys_collection.find_one({
                "user_email": user_email,
                "key_name": key_name,
                "is_deleted": False
            })
            
            if existing:
                logger.warning(f"❌ Key name '{key_name}' already exists for {user_email}")
                return None
            
            # Generate key based on type
            if key_type == "RSA":
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=key_size,
                    backend=default_backend()
                )
                
                # Serialize private key
                private_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                # Serialize public key
                public_key = private_key.public_key()
                public_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                key_material = {
                    "private_key": base64.b64encode(private_pem).decode(),
                    "public_key": base64.b64encode(public_pem).decode()
                }
            
            elif key_type == "AES":
                # Generate AES key (256-bit)
                aes_key = secrets.token_bytes(32)
                key_material = {
                    "key": base64.b64encode(aes_key).decode()
                }
            
            else:
                logger.error(f"❌ Unsupported key type: {key_type}")
                return None
            
            # Create key record
            key_id = f"key_{secrets.token_urlsafe(16)}"
            key_record = {
                "key_id": key_id,
                "user_email": user_email,
                "key_name": key_name,
                "key_type": key_type,
                "key_size": key_size,
                "key_material": key_material,
                "version": 1,
                "versions": [
                    {
                        "version": 1,
                        "created_at": datetime.utcnow(),
                        "key_material": key_material,
                        "is_active": True
                    }
                ],
                "metadata": metadata or {},
                "is_enabled": True,
                "is_deleted": False,
                "rotation_policy": {
                    "enabled": False,
                    "rotation_days": 90
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_rotated": None
            }
            
            await keys_collection.insert_one(key_record)
            
            logger.info(f"✅ Key generated successfully: {key_id}")
            
            # Return key info (without private material)
            return {
                "key_id": key_id,
                "key_name": key_name,
                "key_type": key_type,
                "key_size": key_size,
                "version": 1,
                "public_key": key_material.get("public_key") if key_type == "RSA" else None,
                "created_at": key_record["created_at"],
                "is_enabled": True
            }
            
        except Exception as e:
            logger.error(f"❌ Key generation failed: {str(e)}")
            return None
    
    @staticmethod
    async def get_key(db, user_email: str, key_id: str) -> Optional[Dict]:
        """Retrieve key information"""
        try:
            keys_collection = db["keys"]
            
            key = await keys_collection.find_one({
                "key_id": key_id,
                "user_email": user_email,
                "is_deleted": False
            })
            
            if not key:
                return None
            
            # Return key info without sensitive material
            return {
                "key_id": key["key_id"],
                "key_name": key["key_name"],
                "key_type": key["key_type"],
                "key_size": key["key_size"],
                "version": key["version"],
                "is_enabled": key["is_enabled"],
                "metadata": key["metadata"],
                "created_at": key["created_at"],
                "updated_at": key["updated_at"],
                "last_rotated": key["last_rotated"],
                "rotation_policy": key["rotation_policy"],
                "public_key": key["key_material"].get("public_key") if key["key_type"] == "RSA" else None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve key: {str(e)}")
            return None
    
    @staticmethod
    async def list_keys(db, user_email: str) -> List[Dict]:
        """List all keys for a user"""
        try:
            keys_collection = db["keys"]
            
            keys = await keys_collection.find({
                "user_email": user_email,
                "is_deleted": False
            }).to_list(length=None)
            
            # Return list without sensitive material
            return [
                {
                    "key_id": k["key_id"],
                    "key_name": k["key_name"],
                    "key_type": k["key_type"],
                    "key_size": k["key_size"],
                    "version": k["version"],
                    "is_enabled": k["is_enabled"],
                    "created_at": k["created_at"],
                    "last_rotated": k["last_rotated"]
                }
                for k in keys
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to list keys: {str(e)}")
            return []
    
    @staticmethod
    async def rotate_key(db, user_email: str, key_id: str) -> Optional[Dict]:
        """Rotate a key (create new version)"""
        try:
            logger.info(f"🔄 Rotating key {key_id} for {user_email}")
            
            keys_collection = db["keys"]
            
            key = await keys_collection.find_one({
                "key_id": key_id,
                "user_email": user_email,
                "is_deleted": False
            })
            
            if not key:
                return None
            
            # Generate new key material
            key_type = key["key_type"]
            key_size = key["key_size"]
            
            if key_type == "RSA":
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=key_size,
                    backend=default_backend()
                )
                
                private_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                public_key = private_key.public_key()
                public_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                new_material = {
                    "private_key": base64.b64encode(private_pem).decode(),
                    "public_key": base64.b64encode(public_pem).decode()
                }
            
            elif key_type == "AES":
                aes_key = secrets.token_bytes(32)
                new_material = {
                    "key": base64.b64encode(aes_key).decode()
                }
            
            # Increment version
            new_version = key["version"] + 1
            
            # Mark old versions as inactive
            for v in key["versions"]:
                v["is_active"] = False
            
            # Add new version
            new_version_obj = {
                "version": new_version,
                "created_at": datetime.utcnow(),
                "key_material": new_material,
                "is_active": True
            }
            
            key["versions"].append(new_version_obj)
            
            # Update key record
            await keys_collection.update_one(
                {"key_id": key_id},
                {
                    "$set": {
                        "version": new_version,
                        "key_material": new_material,
                        "versions": key["versions"],
                        "last_rotated": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"✅ Key rotated to version {new_version}")
            
            return {
                "key_id": key_id,
                "key_name": key["key_name"],
                "old_version": key["version"],
                "new_version": new_version,
                "rotated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"❌ Key rotation failed: {str(e)}")
            return None
    
    @staticmethod
    async def delete_key(db, user_email: str, key_id: str) -> bool:
        """Soft delete a key"""
        try:
            keys_collection = db["keys"]
            
            result = await keys_collection.update_one(
                {
                    "key_id": key_id,
                    "user_email": user_email,
                    "is_deleted": False
                },
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow(),
                        "is_enabled": False
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Key deletion failed: {str(e)}")
            return False
    
    @staticmethod
    async def generate_certificate(
        db,
        user_email: str,
        cert_name: str,
        common_name: str,
        validity_days: int = 365,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Generate a self-signed certificate"""
        try:
            logger.info(f"📜 Generating certificate '{cert_name}' for {user_email}")
            
            certs_collection = db["certificates"]
            
            # Check if cert name already exists
            existing = await certs_collection.find_one({
                "user_email": user_email,
                "cert_name": cert_name,
                "is_deleted": False
            })
            
            if existing:
                return None
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CyberSec Platform"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Serialize certificate and key
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            cert_id = f"cert_{secrets.token_urlsafe(16)}"
            
            cert_record = {
                "cert_id": cert_id,
                "user_email": user_email,
                "cert_name": cert_name,
                "common_name": common_name,
                "certificate": base64.b64encode(cert_pem).decode(),
                "private_key": base64.b64encode(key_pem).decode(),
                "serial_number": str(cert.serial_number),
                "not_before": cert.not_valid_before_utc,
                "not_after": cert.not_valid_after_utc,
                "validity_days": validity_days,
                "is_valid": True,
                "is_deleted": False,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "auto_renew": False,
                "renewal_threshold_days": 30
            }
            
            await certs_collection.insert_one(cert_record)
            
            logger.info(f"✅ Certificate generated: {cert_id}")
            
            return {
                "cert_id": cert_id,
                "cert_name": cert_name,
                "common_name": common_name,
                "serial_number": cert_record["serial_number"],
                "not_before": cert_record["not_before"],
                "not_after": cert_record["not_after"],
                "certificate": cert_record["certificate"],
                "created_at": cert_record["created_at"]
            }
            
        except Exception as e:
            logger.error(f"❌ Certificate generation failed: {str(e)}")
            return None
    
    @staticmethod
    async def validate_certificate(db, user_email: str, cert_id: str) -> Dict:
        """Check if certificate is valid and return status"""
        try:
            certs_collection = db["certificates"]
            
            cert = await certs_collection.find_one({
                "cert_id": cert_id,
                "user_email": user_email,
                "is_deleted": False
            })
            
            if not cert:
                return {"valid": False, "reason": "Certificate not found"}
            
            now = datetime.utcnow()
            not_before = cert["not_before"]
            not_after = cert["not_after"]
            
            if now < not_before:
                return {
                    "valid": False,
                    "reason": "Certificate not yet valid",
                    "not_before": not_before
                }
            
            if now > not_after:
                return {
                    "valid": False,
                    "reason": "Certificate expired",
                    "expired_at": not_after
                }
            
            days_until_expiry = (not_after - now).days
            needs_renewal = days_until_expiry <= cert.get("renewal_threshold_days", 30)
            
            return {
                "valid": True,
                "cert_id": cert_id,
                "cert_name": cert["cert_name"],
                "days_until_expiry": days_until_expiry,
                "needs_renewal": needs_renewal,
                "expires_at": not_after
            }
            
        except Exception as e:
            logger.error(f"❌ Certificate validation failed: {str(e)}")
            return {"valid": False, "reason": str(e)}