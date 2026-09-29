from typing import Optional, List
from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field
from app.models.user import UserRole, VerificationStatus, ProfileVisibility

class StudentProfileRead(BaseModel):
    id: int
    user_id: int
    email: Optional[str] = None
    full_name: str
    enrollment_no: Optional[str]
    roll_no: Optional[str]
    course: str
    batch_year: int
    current_semester: int
    cgpa: Optional[float] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    resume_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    custom_links: Optional[str] = None
    skills: Optional[str] = None
    verification_status: str
    show_email: bool
    show_phone: bool

    model_config = ConfigDict(from_attributes=True)

class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    course: Optional[str] = None
    batch_year: Optional[int] = None
    current_semester: Optional[int] = None
    cgpa: Optional[float] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    custom_links: Optional[str] = None
    skills: Optional[str] = None
    show_email: Optional[bool] = None
    show_phone: Optional[bool] = None

class AlumniProjectRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    technologies: str
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    image_url: Optional[str] = None
    role: Optional[str] = None
    completion_year: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class AlumniProjectCreate(BaseModel):
    title: str = Field(..., min_length=2)
    description: Optional[str] = None
    technologies: str = Field(..., min_length=2)
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    role: Optional[str] = "Lead Developer"
    completion_year: Optional[int] = 2024

class AlumniExperienceRead(BaseModel):
    id: int
    company: str
    job_title: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AlumniExperienceCreate(BaseModel):
    company: str
    job_title: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None

class AlumniProfileRead(BaseModel):
    id: int
    user_id: int
    email: Optional[str] = None
    full_name: str
    enrollment_no: Optional[str] = None
    roll_no: Optional[str] = None
    course: str
    batch_year: int
    graduation_year: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    current_company: Optional[str] = None
    current_job_title: Optional[str] = None
    industry: Optional[str] = None
    years_of_experience: float = 1.0
    employment_type: Optional[str] = None
    current_city: Optional[str] = None
    country: Optional[str] = "India"
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    kaggle_url: Optional[str] = None
    hackerrank_url: Optional[str] = None
    stackoverflow_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    custom_links: Optional[str] = None
    skills: Optional[str] = None
    is_mentor: bool = True
    is_referral_provider: bool = True
    is_co_guide: bool = False
    verification_status: str
    verification_notes: Optional[str] = None
    profile_visibility: str
    show_email: bool
    show_phone: bool
    projects: List[AlumniProjectRead] = []
    experiences: List[AlumniExperienceRead] = []

    model_config = ConfigDict(from_attributes=True)

class AlumniProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    course: Optional[str] = None
    batch_year: Optional[int] = None
    graduation_year: Optional[int] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    current_company: Optional[str] = None
    current_job_title: Optional[str] = None
    industry: Optional[str] = None
    years_of_experience: Optional[float] = None
    employment_type: Optional[str] = None
    current_city: Optional[str] = None
    country: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    kaggle_url: Optional[str] = None
    hackerrank_url: Optional[str] = None
    stackoverflow_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    custom_links: Optional[str] = None
    skills: Optional[str] = None
    is_mentor: Optional[bool] = None
    is_referral_provider: Optional[bool] = None
    is_co_guide: Optional[bool] = None
    profile_visibility: Optional[ProfileVisibility] = None
    show_email: Optional[bool] = None
    show_phone: Optional[bool] = None

class VerificationAction(BaseModel):
    status: VerificationStatus
    notes: Optional[str] = None
