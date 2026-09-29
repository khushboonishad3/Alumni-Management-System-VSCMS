import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User, UserRole
from app.models.resource import ResourceCategory, TechnicalResource
from app.schemas.resource import ResourceCreate
from app.core.dependencies import get_current_user, get_optional_current_user, require_roles
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api/resources", tags=["Technical Resource Repository"])

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(ResourceCategory).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "icon": c.icon,
            "count": len(c.resources)
        } for c in cats
    ]

@router.get("")
def get_resources(
    category_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(TechnicalResource).filter(TechnicalResource.is_approved == True)
    
    if category_id:
        query = query.filter(TechnicalResource.category_id == category_id)
    if q:
        query = query.filter(
            TechnicalResource.title.ilike(f"%{q.strip()}%") |
            TechnicalResource.tags.ilike(f"%{q.strip()}%") |
            TechnicalResource.description.ilike(f"%{q.strip()}%")
        )
    if resource_type:
        query = query.filter(TechnicalResource.resource_type.ilike(resource_type.strip()))
        
    resources = query.order_by(TechnicalResource.created_at.desc()).all()
    results = []
    for r in resources:
        uploader_name = "CMS Member"
        if r.uploader and r.uploader.alumni_profile:
            uploader_name = f"{r.uploader.alumni_profile.full_name} (Alumnus)"
        elif r.uploader and r.uploader.student_profile:
            role_label = "Faculty" if r.uploader.role == UserRole.FACULTY else "Student"
            uploader_name = f"{r.uploader.student_profile.full_name} ({role_label})"
        elif r.uploader:
            role_label = "Administrator" if r.uploader.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN] else "CMS Faculty"
            uploader_name = f"{r.uploader.email.split('@')[0].capitalize()} ({role_label})"
            
        results.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "category_id": r.category_id,
            "category_name": r.category.name if r.category else "General",
            "resource_type": r.resource_type,
            "file_url": r.file_url,
            "external_link": r.external_link,
            "tags": [t.strip() for t in r.tags.split(",") if t.strip()],
            "downloads_count": r.downloads_count,
            "uploader_id": r.uploader_id,
            "uploader_name": uploader_name,
            "created_at": r.created_at.isoformat()
        })
    return results

@router.post("")
def upload_resource(
    data: ResourceCreate,
    current_user: User = Depends(require_roles([UserRole.ALUMNI, UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    cat = db.query(ResourceCategory).filter(ResourceCategory.id == data.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
        
    res = TechnicalResource(
        uploader_id=current_user.id,
        category_id=cat.id,
        title=data.title,
        description=data.description,
        resource_type=data.resource_type,
        file_url=data.file_url,
        external_link=data.external_link,
        tags=data.tags,
        is_approved=True
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    
    log_audit_event(db, "UPLOAD_RESOURCE", current_user.id, "TechnicalResource", res.id, None, f"Uploaded {res.title}")
    return {"message": "Resource published successfully!", "id": res.id}

@router.post("/upload-file")
def upload_resource_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.ALUMNI, UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_RESOURCE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension not permitted. Allowed: {list(settings.ALLOWED_RESOURCE_EXTENSIONS)}")
        
    safe_name = f"res_{current_user.id}_{int(os.times().elapsed)}_{file.filename.replace(' ', '_')}"
    dest = settings.RESOURCES_DIR / safe_name
    
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    url = f"/media/resources/{safe_name}"
    return {"url": url, "filename": file.filename}

@router.post("/{resource_id}/download")
def record_download(
    resource_id: int,
    db: Session = Depends(get_db)
):
    res = db.query(TechnicalResource).filter(TechnicalResource.id == resource_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")
    res.downloads_count += 1
    db.commit()
    return {"downloads_count": res.downloads_count}

@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = db.query(TechnicalResource).filter(TechnicalResource.id == resource_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")
    if res.uploader_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
        
    db.delete(res)
    db.commit()
    return {"message": "Resource deleted."}
