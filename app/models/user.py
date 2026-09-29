from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    ALUMNI = "alumni"
    FACULTY = "faculty"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class ProfileVisibility(str, enum.Enum):
    PUBLIC = "public"
    CMS_MEMBERS_ONLY = "cms_members_only"
    CONNECTIONS_ONLY = "connections_only"
    PRIVATE = "private"

class AuthorizedCollegeRegistry(Base):
    """Authorized CMS Kanpur institutional roster for validating enrollment & degree."""
    __tablename__ = "authorized_college_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    enrollment_no = Column(String(50), unique=True, index=True, nullable=False)
    roll_no = Column(String(50), unique=True, index=True, nullable=False)
    course = Column(String(20), nullable=False)  # BCA, MCA
    batch_year = Column(Integer, nullable=False)   # e.g. 2021
    graduation_year = Column(Integer, nullable=False) # e.g. 2024
    status = Column(String(50), default="active")  # active, alumni, graduated
    is_claimed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alumni_profile = relationship("AlumniProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False, index=True)
    enrollment_no = Column(String(50), index=True)
    roll_no = Column(String(50), index=True)
    course = Column(String(20), default="BCA")  # BCA, MCA
    batch_year = Column(Integer, default=2023)
    current_semester = Column(Integer, default=4)
    cgpa = Column(Float, nullable=True)
    phone = Column(String(30), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    resume_url = Column(String(255), nullable=True)
    
    # Developer links
    github_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    leetcode_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    custom_links = Column(Text, nullable=True) # JSON array of {platform, url}
    
    skills = Column(Text, default="Python, SQL, HTML, CSS, JavaScript")  # comma separated
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, index=True)
    verification_notes = Column(Text, nullable=True)
    
    # Privacy
    show_email = Column(Boolean, default=False)
    show_phone = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="student_profile")

class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False, index=True)
    enrollment_no = Column(String(50), index=True)
    roll_no = Column(String(50), index=True)
    course = Column(String(20), default="MCA", index=True)  # BCA, MCA
    batch_year = Column(Integer, default=2020, index=True)
    graduation_year = Column(Integer, default=2023, index=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    
    # Professional fields
    current_company = Column(String(150), index=True)
    current_job_title = Column(String(150), index=True)
    industry = Column(String(100), default="Information Technology")
    years_of_experience = Column(Float, default=1.0)
    employment_type = Column(String(50), default="Full-time")
    current_city = Column(String(100), default="Kanpur", index=True)
    country = Column(String(100), default="India")
    
    # Developer links
    github_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    leetcode_url = Column(String(255), nullable=True)
    kaggle_url = Column(String(255), nullable=True)
    hackerrank_url = Column(String(255), nullable=True)
    stackoverflow_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    custom_links = Column(Text, nullable=True) # JSON array of {platform, url}
    
    # Tech skills & Offerings
    skills = Column(Text, default="Python, Django, React, PostgreSQL")
    is_mentor = Column(Boolean, default=True, index=True)
    is_referral_provider = Column(Boolean, default=True, index=True)
    is_co_guide = Column(Boolean, default=False)
    
    # Verification & Privacy
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, index=True)
    verification_notes = Column(Text, nullable=True)
    profile_visibility = Column(Enum(ProfileVisibility), default=ProfileVisibility.PUBLIC)
    show_email = Column(Boolean, default=False)
    show_phone = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="alumni_profile")
    projects = relationship("AlumniProject", back_populates="alumni", cascade="all, delete-orphan")
    experiences = relationship("AlumniExperience", back_populates="alumni", cascade="all, delete-orphan")
    mentorship_profile = relationship("MentorshipProfile", back_populates="alumni", uselist=False, cascade="all, delete-orphan")

class AlumniProject(Base):
    __tablename__ = "alumni_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    alumni_id = Column(Integer, ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(String(255), nullable=False)  # e.g. "FastAPI, React, Docker"
    github_url = Column(String(255), nullable=True)
    demo_url = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    role = Column(String(100), default="Lead Developer")
    completion_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    alumni = relationship("AlumniProfile", back_populates="projects")

class AlumniExperience(Base):
    __tablename__ = "alumni_experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    alumni_id = Column(Integer, ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(150), nullable=False)
    job_title = Column(String(150), nullable=False)
    location = Column(String(100), nullable=True)
    start_date = Column(String(50), nullable=False) # e.g. "July 2022"
    end_date = Column(String(50), nullable=True)   # "Present" or "May 2024"
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    
    alumni = relationship("AlumniProfile", back_populates="experiences")
