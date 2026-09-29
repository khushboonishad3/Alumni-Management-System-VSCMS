from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class ProjectDifficulty(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ProjectStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ProposalStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class IndustryProject(Base):
    __tablename__ = "industry_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    domain = Column(String(100), default="Web Development / AI", index=True)
    required_technologies = Column(String(255), nullable=False)
    difficulty = Column(Enum(ProjectDifficulty), default=ProjectDifficulty.INTERMEDIATE)
    expected_outcome = Column(Text, nullable=True)
    duration_weeks = Column(Integer, default=8)
    max_students = Column(Integer, default=4)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PROPOSED, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    creator = relationship("User", foreign_keys=[creator_id])
    faculty_guide = relationship("User", foreign_keys=[faculty_id])
    proposals = relationship("ProjectProposal", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")

class ProjectProposal(Base):
    __tablename__ = "project_proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("industry_projects.id", ondelete="CASCADE"), nullable=False)
    student_team_lead_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_members = Column(Text, nullable=False)  # Names & Roll Nos
    proposal_text = Column(Text, nullable=False)
    proposal_document_url = Column(String(255), nullable=True)
    status = Column(Enum(ProposalStatus), default=ProposalStatus.SUBMITTED, index=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    project = relationship("IndustryProject", back_populates="proposals")
    team_lead = relationship("User", foreign_keys=[student_team_lead_id])

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("industry_projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(String(50), nullable=True)
    is_completed = Column(Boolean, default=False)
    submission_url = Column(String(255), nullable=True)
    
    project = relationship("IndustryProject", back_populates="milestones")
