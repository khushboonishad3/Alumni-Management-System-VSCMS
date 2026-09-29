from typing import Optional, List
from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field, EmailStr

class MessageCreate(BaseModel):
    recipient_id: int
    content: str = Field(..., min_length=1)

class MessageRead(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: Optional[str] = None
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationRead(BaseModel):
    id: int
    other_user_id: int
    other_user_name: str
    other_user_role: str
    other_user_avatar: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0

class NotificationRead(BaseModel):
    id: int
    title: str
    message: str
    link: Optional[str] = None
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NewsletterCreate(BaseModel):
    title: str = Field(..., min_length=3)
    content_html: str = Field(..., min_length=10)
    scheduled_for: Optional[datetime] = None

class NewsletterRead(BaseModel):
    id: int
    title: str
    content_html: str
    sent_by_name: Optional[str] = None
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr
