from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole, VerificationStatus

class UserLogin(BaseModel):
    email: str  # Email address, university roll number, or enrollment number
    password: str
    captcha_id: Optional[str] = None
    captcha_code: Optional[str] = None
    remember_me: Optional[bool] = False

class CaptchaResponse(BaseModel):
    captcha_id: str
    captcha_svg: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.STUDENT
    full_name: str = Field(..., min_length=2)
    enrollment_no: str = Field(..., min_length=3)
    roll_no: str = Field(..., min_length=3)
    course: str = "BCA"  # BCA or MCA
    batch_year: int = 2024
    graduation_year: Optional[int] = None
    personal_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    # Optional Alumni fields on registration
    current_company: Optional[str] = None
    current_job_title: Optional[str] = None
    skills: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str
    full_name: str
    is_verified: bool
    verification_status: str
    redirect_view: Optional[str] = "home"

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    email: str
    reset_code: str
    new_password: str = Field(..., min_length=6)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
