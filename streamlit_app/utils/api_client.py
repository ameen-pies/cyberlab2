import requests
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
env_path = project_root / '.env'
load_dotenv(env_path)

from shared.config.settings import settings
# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.config.settings import settings
from typing import Optional

class APIClient:
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.token: Optional[str] = None
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
    
    def get_headers(self):
        """Get request headers with auth token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def register(self, email: str, password: str, full_name: str):
        """Register new user"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name
                }
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def login(self, email: str, password: str):
        """Login user"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def send_mfa_code(self, email: str):
        """Request MFA code"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/mfa/send",
                json={"email": email}
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def verify_mfa_code(self, email: str, code: str):
        """Verify MFA code and get token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/mfa/verify",
                json={
                    "email": email,
                    "code": code
                }
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def encrypt_in_transit(self, data: str, password: str):
        """Encrypt data in transit"""
        try:
            response = requests.post(
                f"{self.base_url}/simulations/encrypt/in-transit",
                json={
                    "data": data,
                    "password": password
                },
                headers=self.get_headers()
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def decrypt_in_transit(self, encrypted_data: str, password: str, salt: str):
        """Decrypt data in transit"""
        try:
            response = requests.post(
                f"{self.base_url}/simulations/decrypt/in-transit",
                json={
                    "encrypted_data": encrypted_data,
                    "password": password,
                    "salt": salt
                },
                headers=self.get_headers()
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def encrypt_at_rest(self, data: str):
        """Encrypt data at rest"""
        try:
            response = requests.post(
                f"{self.base_url}/simulations/encrypt/at-rest",
                json={"data": data},
                headers=self.get_headers()
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def decrypt_at_rest(self, encrypted_data: str, key: str):
        """Decrypt data at rest"""
        try:
            response = requests.post(
                f"{self.base_url}/simulations/decrypt/at-rest",
                json={
                    "encrypted_data": encrypted_data,
                    "key": key
                },
                headers=self.get_headers()
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500
    
    def encryption_lifecycle(self, data: str):
        """Get full encryption lifecycle demo"""
        try:
            response = requests.post(
                f"{self.base_url}/simulations/encrypt/lifecycle",
                json={"data": data},
                headers=self.get_headers()
            )
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500