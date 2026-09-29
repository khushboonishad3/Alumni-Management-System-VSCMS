from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ResourceCategory(Base):
    __tablename__ = "resource_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    icon = Column(String(50), default="folder")
    
    resources = relationship("TechnicalResource", back_populates="category", cascade="all, delete-orphan")

class TechnicalResource(Base):
    __tablename__ = "technical_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("resource_categories.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    resource_type = Column(String(50), default="PDF") # PDF, CODE, CHEATSHEET, VIDEO, LINK, DOC
    file_url = Column(String(255), nullable=True)
    external_link = Column(String(255), nullable=True)
    tags = Column(String(255), default="Interview, BCA, MCA, DSA")
    downloads_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    uploader = relationship("User")
    category = relationship("ResourceCategory", back_populates="resources")
