from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    email: EmailStr
    full_name: str
    hashed_password: str
    is_verified: bool = False
    mfa_enabled: bool = True
    mfa_secret: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "hashed_password": "hashed_password_here",
                "is_verified": True,
                "mfa_enabled": True
            }
        }