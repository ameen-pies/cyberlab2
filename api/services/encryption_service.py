from api.utils.crypto import (
    encrypt_data, 
    decrypt_data, 
    generate_key_from_password,
    generate_random_key
)
import base64
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    @staticmethod
    def encrypt_in_transit(data: str, password: str) -> dict:
        """Simulate encryption in transit (TLS/SSL)"""
        try:
            key, salt = generate_key_from_password(password)
            encrypted = encrypt_data(data, key)
            
            return {
                "success": True,
                "encrypted_data": encrypted,
                "salt": base64.b64encode(salt).decode(),
                "method": "AES-256 (Fernet)",
                "use_case": "In Transit - Simulating TLS/SSL encryption"
            }
        except Exception as e:
            logger.error(f"Encryption in transit failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def decrypt_in_transit(encrypted_data: str, password: str, salt_b64: str) -> dict:
        """Decrypt data encrypted in transit"""
        try:
            salt = base64.b64decode(salt_b64)
            key, _ = generate_key_from_password(password, salt)
            decrypted = decrypt_data(encrypted_data, key)
            
            return {
                "success": True,
                "decrypted_data": decrypted,
                "method": "AES-256 (Fernet)"
            }
        except Exception as e:
            logger.error(f"Decryption in transit failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def encrypt_at_rest(data: str) -> dict:
        """Simulate encryption at rest (database encryption)"""
        try:
            key = generate_random_key()
            encrypted = encrypt_data(data, key)
            
            return {
                "success": True,
                "encrypted_data": encrypted,
                "key": key.decode(),
                "method": "AES-256 (Fernet)",
                "use_case": "At Rest - Database/File encryption",
                "note": "In production, keys would be stored in a secure key management system (KMS)"
            }
        except Exception as e:
            logger.error(f"Encryption at rest failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def decrypt_at_rest(encrypted_data: str, key_str: str) -> dict:
        """Decrypt data encrypted at rest"""
        try:
            key = key_str.encode()
            decrypted = decrypt_data(encrypted_data, key)
            
            return {
                "success": True,
                "decrypted_data": decrypted,
                "method": "AES-256 (Fernet)"
            }
        except Exception as e:
            logger.error(f"Decryption at rest failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def demonstrate_encryption_lifecycle(sample_data: str) -> dict:
        """Complete demonstration of encryption lifecycle"""
        try:
            # Encrypt at rest
            at_rest = EncryptionService.encrypt_at_rest(sample_data)
            
            # Simulate retrieval and decryption
            decrypted_at_rest = EncryptionService.decrypt_at_rest(
                at_rest["encrypted_data"],
                at_rest["key"]
            )
            
            # Encrypt for transit
            in_transit = EncryptionService.encrypt_in_transit(
                decrypted_at_rest["decrypted_data"],
                "secure_transport_password"
            )
            
            return {
                "success": True,
                "stages": {
                    "1_at_rest_encryption": at_rest,
                    "2_at_rest_decryption": decrypted_at_rest,
                    "3_in_transit_encryption": in_transit
                },
                "explanation": {
                    "at_rest": "Data encrypted in database/storage using generated key",
                    "in_transit": "Data encrypted during transmission using password-derived key",
                    "real_world": "In production: At-rest uses KMS, In-transit uses TLS/SSL"
                }
            }
        except Exception as e:
            logger.error(f"Encryption lifecycle demo failed: {str(e)}")
            return {"success": False, "error": str(e)}