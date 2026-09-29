from typing import Optional
from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field

class ResourceCategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: str

    model_config = ConfigDict(from_attributes=True)

class ResourceCreate(BaseModel):
    category_id: int
    title: str = Field(..., min_length=3)
    description: Optional[str] = None
    resource_type: str = "PDF"
    file_url: Optional[str] = None
    external_link: Optional[str] = None
    tags: str = "BCA, MCA, Interview Prep"

class ResourceRead(BaseModel):
    id: int
    uploader_id: int
    uploader_name: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    resource_type: str
    file_url: Optional[str] = None
    external_link: Optional[str] = None
    tags: str
    downloads_count: int
    is_approved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
