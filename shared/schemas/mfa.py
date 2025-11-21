from pydantic import BaseModel, EmailStr

class MFARequest(BaseModel):
    email: EmailStr

class MFAVerify(BaseModel):
    email: EmailStr
    code: str

class MFAResponse(BaseModel):
    success: bool
    message: str