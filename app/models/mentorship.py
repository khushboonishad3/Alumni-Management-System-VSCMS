from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class MentorshipStatus(str, enum.Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"

class SessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InterviewType(str, enum.Enum):
    TECHNICAL = "technical"
    HR = "hr"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"
    RESUME_BASED = "resume_based"

class ReviewStatus(str, enum.Enum):
    REQUESTED = "requested"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"

class MentorshipProfile(Base):
    __tablename__ = "mentorship_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    alumni_id = Column(Integer, ForeignKey("alumni_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    topics = Column(String(255), default="DSA, Web Development, Career Strategy, LeetCode")
    bio = Column(Text, nullable=True)
    max_mentees = Column(Integer, default=5)
    meeting_format = Column(String(100), default="Google Meet / 1-on-1 Virtual")
    availability_details = Column(String(200), default="Weekends: 10 AM - 1 PM")
    is_active = Column(Boolean, default=True)
    
    alumni = relationship("AlumniProfile", back_populates="mentorship_profile")

class MentorshipRequest(Base):
    __tablename__ = "mentorship_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mentee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(MentorshipStatus), default=MentorshipStatus.REQUESTED, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    mentor = relationship("User", foreign_keys=[mentor_id])
    mentee = relationship("User", foreign_keys=[mentee_id])
    sessions = relationship("MentorshipSession", back_populates="request", cascade="all, delete-orphan")

class MentorshipSession(Base):
    __tablename__ = "mentorship_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("mentorship_requests.id", ondelete="CASCADE"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=45)
    meeting_link = Column(String(255), nullable=True)
    agenda = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    mentee_rating = Column(Float, nullable=True)
    mentee_feedback = Column(Text, nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    request = relationship("MentorshipRequest", back_populates="sessions")

class MockInterview(Base):
    __tablename__ = "mock_interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    interviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    interviewee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    interview_type = Column(Enum(InterviewType), default=InterviewType.TECHNICAL, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    meeting_link = Column(String(255), nullable=True)
    status = Column(String(50), default="requested", index=True) # requested, scheduled, completed, cancelled
    feedback = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    interviewee = relationship("User", foreign_keys=[interviewee_id])

class ResumeReview(Base):
    __tablename__ = "resume_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_url = Column(String(255), nullable=False)
    target_roles = Column(String(200), default="Full Stack Developer, SDE-1")
    review_comments = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.REQUESTED, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    student = relationship("User", foreign_keys=[student_id])
