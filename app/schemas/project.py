from typing import Optional, List
from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field
from app.models.project import ProjectDifficulty, ProjectStatus, ProposalStatus

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    domain: str = "Web Development / AI"
    required_technologies: str = "FastAPI, PostgreSQL, React"
    difficulty: ProjectDifficulty = ProjectDifficulty.INTERMEDIATE
    expected_outcome: Optional[str] = None
    duration_weeks: int = 8
    max_students: int = 4

class ProjectProposalCreate(BaseModel):
    team_members: str
    proposal_text: str = Field(..., min_length=15)
    proposal_document_url: Optional[str] = None

class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None

class ProjectMilestoneRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    is_completed: bool
    submission_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProjectProposalRead(BaseModel):
    id: int
    project_id: int
    student_team_lead_id: int
    team_lead_name: Optional[str] = None
    team_members: str
    proposal_text: str
    proposal_document_url: Optional[str] = None
    status: ProposalStatus
    feedback: Optional[str] = None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectRead(BaseModel):
    id: int
    creator_id: int
    creator_name: Optional[str] = None
    creator_company: Optional[str] = None
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    title: str
    description: str
    domain: str
    required_technologies: str
    difficulty: ProjectDifficulty
    expected_outcome: Optional[str] = None
    duration_weeks: int
    max_students: int
    status: ProjectStatus
    created_at: datetime
    proposals_count: int = 0
    milestones: List[ProjectMilestoneRead] = []

    model_config = ConfigDict(from_attributes=True)
