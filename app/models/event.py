from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class EventType(str, enum.Enum):
    HACKATHON = "hackathon"
    CODING_COMPETITION = "coding_competition"
    TECH_FEST = "tech_fest"
    WORKSHOP = "workshop"
    WEBINAR = "webinar"
    GUEST_LECTURE = "guest_lecture"
    ALUMNI_MEET = "alumni_meet"

class EventRole(str, enum.Enum):
    ATTENDEE = "attendee"
    JUDGE = "judge"
    MENTOR = "mentor"
    SPEAKER = "speaker"
    SPONSOR = "sponsor"
    ORGANIZER = "organizer"

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    event_type = Column(Enum(EventType), default=EventType.WEBINAR, nullable=False, index=True)
    description = Column(Text, nullable=False)
    venue_or_link = Column(String(255), default="CMS Kanpur Auditorium / Google Meet")
    is_online = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    capacity = Column(Integer, default=150)
    registration_deadline = Column(DateTime, nullable=True)
    banner_image = Column(String(255), nullable=True)
    speaker_info = Column(String(255), nullable=True)
    is_published = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    organizer = relationship("User", foreign_keys=[organizer_id])
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")

class EventRegistration(Base):
    __tablename__ = "event_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    role_in_event = Column(Enum(EventRole), default=EventRole.ATTENDEE, nullable=False)
    attended = Column(Boolean, default=False)
    feedback = Column(Text, nullable=True)
    
    event = relationship("Event", back_populates="registrations")
    user = relationship("User")
