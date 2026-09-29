from app.database import Base
from app.models.user import (
    User, UserRole, VerificationStatus, ProfileVisibility,
    AuthorizedCollegeRegistry, StudentProfile, AlumniProfile,
    AlumniProject, AlumniExperience
)
from app.models.job import (
    Job, JobType, LocationType, ApplicationStatus,
    ReferralStatus, JobApplication, ReferralRequest, SavedJob
)
from app.models.mentorship import (
    MentorshipProfile, MentorshipRequest, MentorshipSession,
    MockInterview, ResumeReview, MentorshipStatus, SessionStatus,
    InterviewType, ReviewStatus
)
from app.models.project import (
    IndustryProject, ProjectProposal, ProjectMilestone,
    ProjectDifficulty, ProjectStatus, ProposalStatus
)
from app.models.resource import ResourceCategory, TechnicalResource
from app.models.event import Event, EventRegistration, EventType, EventRole
from app.models.communication import Conversation, Message, Notification, Newsletter, NewsletterSubscriber
from app.models.audit import AuditLog, UserReport

__all__ = [
    "Base",
    "User", "UserRole", "VerificationStatus", "ProfileVisibility",
    "AuthorizedCollegeRegistry", "StudentProfile", "AlumniProfile",
    "AlumniProject", "AlumniExperience",
    "Job", "JobType", "LocationType", "ApplicationStatus",
    "ReferralStatus", "JobApplication", "ReferralRequest", "SavedJob",
    "MentorshipProfile", "MentorshipRequest", "MentorshipSession",
    "MockInterview", "ResumeReview", "MentorshipStatus", "SessionStatus",
    "InterviewType", "ReviewStatus",
    "IndustryProject", "ProjectProposal", "ProjectMilestone",
    "ProjectDifficulty", "ProjectStatus", "ProposalStatus",
    "ResourceCategory", "TechnicalResource",
    "Event", "EventRegistration", "EventType", "EventRole",
    "Conversation", "Message", "Notification", "Newsletter", "NewsletterSubscriber",
    "AuditLog", "UserReport"
]
