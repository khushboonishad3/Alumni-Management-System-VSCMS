from app.schemas.auth import (
    UserLogin, UserRegister, TokenResponse, PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest
)
from app.schemas.user import (
    StudentProfileRead, StudentProfileUpdate, AlumniProfileRead, AlumniProfileUpdate,
    AlumniProjectRead, AlumniProjectCreate, AlumniExperienceRead, AlumniExperienceCreate,
    VerificationAction
)
from app.schemas.job import (
    JobCreate, JobUpdate, JobRead, JobApplicationCreate, JobApplicationRead,
    ApplicationStatusUpdate, ReferralRequestCreate, ReferralRequestUpdate, ReferralRequestRead
)
from app.schemas.mentorship import (
    MentorshipProfileUpdate, MentorshipProfileRead, MentorshipRequestCreate,
    MentorshipRequestUpdate, MentorshipSessionCreate, MentorshipSessionRead,
    MentorshipRequestRead, MockInterviewCreate, MockInterviewRead,
    ResumeReviewCreate, ResumeReviewRead
)
from app.schemas.project import (
    ProjectCreate, ProjectRead, ProjectProposalCreate, ProjectProposalRead,
    MilestoneCreate, ProjectMilestoneRead
)
from app.schemas.resource import ResourceCategoryRead, ResourceCreate, ResourceRead
from app.schemas.event import EventCreate, EventRead, EventRegisterRequest, EventRegistrationRead
from app.schemas.communication import (
    MessageCreate, MessageRead, ConversationRead, NotificationRead,
    NewsletterCreate, NewsletterRead, NewsletterSubscribeRequest
)

__all__ = [
    "UserLogin", "UserRegister", "TokenResponse", "PasswordResetRequest", "PasswordResetConfirm", "ChangePasswordRequest",
    "StudentProfileRead", "StudentProfileUpdate", "AlumniProfileRead", "AlumniProfileUpdate",
    "AlumniProjectRead", "AlumniProjectCreate", "AlumniExperienceRead", "AlumniExperienceCreate",
    "VerificationAction",
    "JobCreate", "JobUpdate", "JobRead", "JobApplicationCreate", "JobApplicationRead",
    "ApplicationStatusUpdate", "ReferralRequestCreate", "ReferralRequestUpdate", "ReferralRequestRead",
    "MentorshipProfileUpdate", "MentorshipProfileRead", "MentorshipRequestCreate",
    "MentorshipRequestUpdate", "MentorshipSessionCreate", "MentorshipSessionRead",
    "MentorshipRequestRead", "MockInterviewCreate", "MockInterviewRead",
    "ResumeReviewCreate", "ResumeReviewRead",
    "ProjectCreate", "ProjectRead", "ProjectProposalCreate", "ProjectProposalRead",
    "MilestoneCreate", "ProjectMilestoneRead",
    "ResourceCategoryRead", "ResourceCreate", "ResourceRead",
    "EventCreate", "EventRead", "EventRegisterRequest", "EventRegistrationRead",
    "MessageCreate", "MessageRead", "ConversationRead", "NotificationRead",
    "NewsletterCreate", "NewsletterRead", "NewsletterSubscribeRequest"
]
