from typing import Optional, List
from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field
from app.models.job import JobType, LocationType, ApplicationStatus, ReferralStatus

class JobCreate(BaseModel):
    title: str = Field(..., min_length=2)
    company: str = Field(..., min_length=2)
    job_type: JobType = JobType.FULL_TIME
    location_type: LocationType = LocationType.HYBRID
    location: str = "Noida / Hybrid"
    experience_required: str = "0-2 Years"
    salary_range: Optional[str] = "6 - 10 LPA"
    required_skills: str = "Python, SQL, React"
    description: str = Field(..., min_length=10)
    external_apply_url: Optional[str] = None
    deadline: Optional[str] = None
    is_referral_available: bool = True

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    job_type: Optional[JobType] = None
    location_type: Optional[LocationType] = None
    location: Optional[str] = None
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    required_skills: Optional[str] = None
    description: Optional[str] = None
    external_apply_url: Optional[str] = None
    deadline: Optional[str] = None
    is_referral_available: Optional[bool] = None
    is_active: Optional[bool] = None

class JobRead(BaseModel):
    id: int
    poster_id: int
    poster_name: Optional[str] = None
    title: str
    company: str
    job_type: JobType
    location_type: LocationType
    location: str
    experience_required: str
    salary_range: Optional[str] = None
    required_skills: str
    description: str
    external_apply_url: Optional[str] = None
    deadline: Optional[str] = None
    is_referral_available: bool
    is_active: bool
    created_at: datetime
    applications_count: int = 0
    is_saved: bool = False

    model_config = ConfigDict(from_attributes=True)

class JobApplicationCreate(BaseModel):
    resume_url: Optional[str] = None
    cover_note: Optional[str] = None

class JobApplicationRead(BaseModel):
    id: int
    job_id: int
    job_title: Optional[str] = None
    company: Optional[str] = None
    applicant_id: int
    applicant_name: Optional[str] = None
    applicant_course: Optional[str] = None
    resume_url: Optional[str] = None
    cover_note: Optional[str] = None
    status: ApplicationStatus
    applied_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus

class ReferralRequestCreate(BaseModel):
    alumni_id: int
    job_id: Optional[int] = None
    target_company: str
    target_role: str
    resume_url: Optional[str] = None
    note: Optional[str] = None

class ReferralRequestUpdate(BaseModel):
    status: ReferralStatus
    feedback: Optional[str] = None

class ReferralRequestRead(BaseModel):
    id: int
    job_id: Optional[int] = None
    alumni_id: int
    alumni_name: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    student_course: Optional[str] = None
    target_company: str
    target_role: str
    resume_url: Optional[str] = None
    note: Optional[str] = None
    status: ReferralStatus
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
