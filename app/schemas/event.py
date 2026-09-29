from typing import Optional, List
from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field
from app.models.event import EventType, EventRole

class EventCreate(BaseModel):
    title: str = Field(..., min_length=3)
    event_type: EventType = EventType.WEBINAR
    description: str = Field(..., min_length=10)
    venue_or_link: str = "CMS Kanpur Auditorium / Google Meet"
    is_online: bool = False
    start_time: datetime
    end_time: datetime
    capacity: int = 150
    registration_deadline: Optional[datetime] = None
    banner_image: Optional[str] = None
    speaker_info: Optional[str] = None

class EventRegisterRequest(BaseModel):
    role_in_event: EventRole = EventRole.ATTENDEE

class EventRegistrationRead(BaseModel):
    id: int
    event_id: int
    user_id: int
    user_name: Optional[str] = None
    role_in_event: EventRole
    registered_at: datetime
    attended: bool

    model_config = ConfigDict(from_attributes=True)

class EventRead(BaseModel):
    id: int
    organizer_id: int
    organizer_name: Optional[str] = None
    title: str
    event_type: EventType
    description: str
    venue_or_link: str
    is_online: bool
    start_time: datetime
    end_time: datetime
    capacity: int
    registration_deadline: Optional[datetime] = None
    banner_image: Optional[str] = None
    speaker_info: Optional[str] = None
    is_published: bool
    created_at: datetime
    registrations_count: int = 0
    is_registered: bool = False

    model_config = ConfigDict(from_attributes=True)
