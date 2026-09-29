from typing import Optional, List
from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field
from app.models.mentorship import MentorshipStatus, SessionStatus, InterviewType, ReviewStatus

class MentorshipProfileUpdate(BaseModel):
    topics: Optional[str] = None
    bio: Optional[str] = None
    max_mentees: Optional[int] = 5
    meeting_format: Optional[str] = "Google Meet / 1-on-1 Virtual"
    availability_details: Optional[str] = "Weekends: 10 AM - 1 PM"
    is_active: Optional[bool] = True

class MentorshipProfileRead(BaseModel):
    id: int
    alumni_id: int
    alumni_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    topics: str
    bio: Optional[str] = None
    max_mentees: int
    meeting_format: str
    availability_details: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class MentorshipRequestCreate(BaseModel):
    mentor_id: int
    topic: str
    message: str = Field(..., min_length=10)

class MentorshipRequestUpdate(BaseModel):
    status: MentorshipStatus

class MentorshipSessionCreate(BaseModel):
    scheduled_at: datetime
    duration_minutes: int = 45
    meeting_link: Optional[str] = "https://meet.google.com/cms-alumni-session"
    agenda: Optional[str] = None

class MentorshipSessionRead(BaseModel):
    id: int
    request_id: int
    scheduled_at: datetime
    duration_minutes: int
    meeting_link: Optional[str] = None
    agenda: Optional[str] = None
    notes: Optional[str] = None
    mentee_rating: Optional[float] = None
    mentee_feedback: Optional[str] = None
    status: SessionStatus

    model_config = ConfigDict(from_attributes=True)

class MentorshipRequestRead(BaseModel):
    id: int
    mentor_id: int
    mentor_name: Optional[str] = None
    mentee_id: int
    mentee_name: Optional[str] = None
    mentee_course: Optional[str] = None
    topic: str
    message: str
    status: MentorshipStatus
    created_at: datetime
    sessions: List[MentorshipSessionRead] = []

    model_config = ConfigDict(from_attributes=True)

class MockInterviewCreate(BaseModel):
    interviewer_id: int
    interview_type: InterviewType = InterviewType.TECHNICAL
    preferred_date: Optional[str] = None
    note: Optional[str] = None

class MockInterviewRead(BaseModel):
    id: int
    interviewer_id: int
    interviewer_name: Optional[str] = None
    interviewee_id: int
    interviewee_name: Optional[str] = None
    interview_type: InterviewType
    scheduled_at: Optional[datetime] = None
    meeting_link: Optional[str] = None
    status: str
    feedback: Optional[str] = None
    rating: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResumeReviewCreate(BaseModel):
    reviewer_id: int
    resume_url: str
    target_roles: str = "Full Stack Developer, SDE-1"

class ResumeReviewRead(BaseModel):
    id: int
    reviewer_id: int
    reviewer_name: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    resume_url: str
    target_roles: str
    review_comments: Optional[str] = None
    suggestions: Optional[str] = None
    status: ReviewStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
