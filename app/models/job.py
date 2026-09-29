from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    CONTRACT = "contract"

class LocationType(str, enum.Enum):
    ON_SITE = "on_site"
    HYBRID = "hybrid"
    REMOTE = "remote"

class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

class ReferralStatus(str, enum.Enum):
    REQUESTED = "requested"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REFERRED = "referred"
    INTERVIEW = "interview"
    SELECTED = "selected"
    CLOSED = "closed"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    poster_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    company = Column(String(150), nullable=False, index=True)
    job_type = Column(Enum(JobType), default=JobType.FULL_TIME, nullable=False, index=True)
    location_type = Column(Enum(LocationType), default=LocationType.HYBRID, nullable=False)
    location = Column(String(100), default="Noida / Hybrid")
    experience_required = Column(String(50), default="0-2 Years")
    salary_range = Column(String(100), nullable=True)  # e.g. "6 - 10 LPA" or "Stipend: 25k/mo"
    required_skills = Column(String(255), nullable=False) # e.g. "Python, Django, PostgreSQL"
    description = Column(Text, nullable=False)
    external_apply_url = Column(String(255), nullable=True)
    deadline = Column(String(50), nullable=True)
    is_referral_available = Column(Boolean, default=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    poster = relationship("User", foreign_keys=[poster_id])
    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")
    saved_by = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_url = Column(String(255), nullable=True)
    cover_note = Column(Text, nullable=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED, index=True)
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    job = relationship("Job", back_populates="applications")
    applicant = relationship("User", foreign_keys=[applicant_id])

class ReferralRequest(Base):
    __tablename__ = "referral_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    alumni_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_company = Column(String(150), nullable=False)
    target_role = Column(String(150), nullable=False)
    resume_url = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.REQUESTED, index=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    alumni = relationship("User", foreign_keys=[alumni_id])
    student = relationship("User", foreign_keys=[student_id])
    job = relationship("Job", foreign_keys=[job_id])

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    saved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    job = relationship("Job", back_populates="saved_by")
    user = relationship("User")
