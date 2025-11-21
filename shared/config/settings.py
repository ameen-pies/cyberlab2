from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str
    DATABASE_NAME: str = "cybersec_platform"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    
    # Frontend
    STREAMLIT_SERVER_PORT: int = 8501
    API_BASE_URL: str = "http://localhost:8000"
    
    # MFA
    MFA_ISSUER: str = "CyberSecPlatform"
    MFA_CODE_EXPIRY: int = 300
    
    # Redis
    REDIS_HOST: Optional[str] = "localhost"
    REDIS_PORT: Optional[int] = 6379
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()