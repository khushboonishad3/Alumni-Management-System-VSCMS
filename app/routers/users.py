import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.config import settings
from app.models.user import (
    User, UserRole, VerificationStatus, ProfileVisibility,
    StudentProfile, AlumniProfile, AlumniProject, AlumniExperience
)
from app.schemas.user import (
    AlumniProfileRead, AlumniProfileUpdate, StudentProfileRead, StudentProfileUpdate,
    AlumniProjectCreate, AlumniProjectRead, AlumniExperienceCreate, AlumniExperienceRead
)
from app.core.dependencies import get_current_user, get_optional_current_user
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api", tags=["Users & Alumni Directory"])

@router.get("/alumni")
def get_alumni_directory(
    q: Optional[str] = Query(None, description="General search by name, company, or title"),
    course: Optional[str] = Query(None, description="Course filter: BCA or MCA"),
    batch_from: Optional[int] = Query(None, description="Start batch year"),
    batch_to: Optional[int] = Query(None, description="End batch year"),
    technology: Optional[str] = Query(None, description="Specific technology skill e.g. Python, React"),
    company: Optional[str] = Query(None, description="Current company"),
    job_title: Optional[str] = Query(None, description="Job role"),
    city: Optional[str] = Query(None, description="Current city"),
    mentorship: Optional[bool] = Query(None, description="Available for mentorship"),
    referral: Optional[bool] = Query(None, description="Available for job referral"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Advanced searchable alumni directory with multi-filter support for CMS Kanpur BCA & MCA."""
    query = db.query(AlumniProfile).join(User, AlumniProfile.user_id == User.id)
    
    # Exclude suspended or inactive users
    query = query.filter(User.is_active == True)
    
    # 1. Search query (Name, Company, Job Title, Skills)
    if q:
        search_fmt = f"%{q.strip()}%"
        query = query.filter(
            or_(
                AlumniProfile.full_name.ilike(search_fmt),
                AlumniProfile.current_company.ilike(search_fmt),
                AlumniProfile.current_job_title.ilike(search_fmt),
                AlumniProfile.skills.ilike(search_fmt),
                AlumniProfile.current_city.ilike(search_fmt)
            )
        )
    
    # 2. Course (BCA or MCA)
    if course:
        query = query.filter(AlumniProfile.course.ilike(course.strip()))
        
    # 3. Batch year range (e.g. 2020 - 2024)
    if batch_from:
        query = query.filter(AlumniProfile.batch_year >= batch_from)
    if batch_to:
        query = query.filter(AlumniProfile.batch_year <= batch_to)
        
    # 4. Specific technology tag
    if technology:
        tech_fmt = f"%{technology.strip()}%"
        query = query.filter(AlumniProfile.skills.ilike(tech_fmt))
        
    # 5. Company
    if company:
        query = query.filter(AlumniProfile.current_company.ilike(f"%{company.strip()}%"))
        
    # 6. Job title
    if job_title:
        query = query.filter(AlumniProfile.current_job_title.ilike(f"%{job_title.strip()}%"))
        
    # 7. City
    if city:
        query = query.filter(AlumniProfile.current_city.ilike(f"%{city.strip()}%"))
        
    # 8. Mentorship availability
    if mentorship is not None:
        query = query.filter(AlumniProfile.is_mentor == mentorship)
        
    # 9. Referral availability
    if referral is not None:
        query = query.filter(AlumniProfile.is_referral_provider == referral)
        
    total_count = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(AlumniProfile.batch_year.desc(), AlumniProfile.full_name.asc()).offset(offset).limit(page_size).all()
    
    results = []
    for item in items:
        # Respect individual privacy choices
        can_view_contact = (
            current_user and (
                current_user.id == item.user_id or 
                current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
            )
        )
        email_val = item.user.email if (can_view_contact or item.show_email) else None
        phone_val = item.phone if (can_view_contact or item.show_phone) else None
        
        results.append({
            "id": item.id,
            "user_id": item.user_id,
            "full_name": item.full_name,
            "course": item.course,
            "batch_year": item.batch_year,
            "graduation_year": item.graduation_year,
            "bio": item.bio,
            "avatar_url": item.avatar_url,
            "current_company": item.current_company,
            "current_job_title": item.current_job_title,
            "industry": item.industry,
            "years_of_experience": item.years_of_experience,
            "current_city": item.current_city,
            "country": item.country,
            "skills": [s.strip() for s in item.skills.split(",") if s.strip()] if item.skills else [],
            "skills_raw": item.skills,
            "is_mentor": item.is_mentor,
            "is_referral_provider": item.is_referral_provider,
            "is_co_guide": item.is_co_guide,
            "verification_status": item.verification_status.value,
            "is_verified": item.verification_status == VerificationStatus.VERIFIED,
            "github_url": item.github_url,
            "linkedin_url": item.linkedin_url,
            "leetcode_url": item.leetcode_url,
            "portfolio_url": item.portfolio_url,
            "email": email_val,
            "phone": phone_val
        })
        
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
        "items": results
    }

@router.get("/alumni/{alumni_id}")
def get_alumni_detail(
    alumni_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(AlumniProfile).filter(AlumniProfile.id == alumni_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Alumni profile not found.")
    
    can_view_contact = (
        current_user and (
            current_user.id == profile.user_id or 
            current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        )
    )
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "course": profile.course,
        "batch_year": profile.batch_year,
        "graduation_year": profile.graduation_year,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "current_company": profile.current_company,
        "current_job_title": profile.current_job_title,
        "industry": profile.industry,
        "years_of_experience": profile.years_of_experience,
        "employment_type": profile.employment_type,
        "current_city": profile.current_city,
        "country": profile.country,
        "skills": [s.strip() for s in profile.skills.split(",") if s.strip()] if profile.skills else [],
        "skills_raw": profile.skills,
        "is_mentor": profile.is_mentor,
        "is_referral_provider": profile.is_referral_provider,
        "is_co_guide": profile.is_co_guide,
        "verification_status": profile.verification_status.value,
        "is_verified": profile.verification_status == VerificationStatus.VERIFIED,
        "verification_notes": profile.verification_notes,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "leetcode_url": profile.leetcode_url,
        "kaggle_url": profile.kaggle_url,
        "hackerrank_url": profile.hackerrank_url,
        "stackoverflow_url": profile.stackoverflow_url,
        "portfolio_url": profile.portfolio_url,
        "custom_links": profile.custom_links,
        "email": profile.user.email if (can_view_contact or profile.show_email) else None,
        "phone": profile.phone if (can_view_contact or profile.show_phone) else None,
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "technologies": p.technologies,
                "github_url": p.github_url,
                "demo_url": p.demo_url,
                "role": p.role,
                "completion_year": p.completion_year
            } for p in profile.projects
        ],
        "experiences": [
            {
                "id": e.id,
                "company": e.company,
                "job_title": e.job_title,
                "location": e.location,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "is_current": e.is_current,
                "description": e.description
            } for e in profile.experiences
        ]
    }

@router.put("/alumni/profile")
def update_alumni_profile(
    data: AlumniProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Alumni profile not found for this account.")
    
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, val)
        
    db.commit()
    db.refresh(profile)
    log_audit_event(db, "UPDATE_PROFILE", current_user.id, "AlumniProfile", profile.id, None, "Updated alumni profile")
    return {"message": "Profile updated successfully.", "profile_id": profile.id}

@router.post("/alumni/projects")
def add_alumni_project(
    data: AlumniProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Only alumni profiles can showcase projects.")
    
    proj = AlumniProject(
        alumni_id=profile.id,
        title=data.title,
        description=data.description,
        technologies=data.technologies,
        github_url=data.github_url,
        demo_url=data.demo_url,
        role=data.role,
        completion_year=data.completion_year
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return {"message": "Project added successfully.", "id": proj.id}

@router.delete("/alumni/projects/{project_id}")
def delete_alumni_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(AlumniProject).filter(AlumniProject.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    if proj.alumni.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    db.delete(proj)
    db.commit()
    return {"message": "Project deleted."}

@router.post("/alumni/experiences")
def add_alumni_experience(
    data: AlumniExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Only alumni can add career experiences.")
    
    exp = AlumniExperience(
        alumni_id=profile.id,
        company=data.company,
        job_title=data.job_title,
        location=data.location,
        start_date=data.start_date,
        end_date=data.end_date,
        is_current=data.is_current,
        description=data.description
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return {"message": "Experience added.", "id": exp.id}

@router.put("/alumni/experiences/{exp_id}")
def update_alumni_experience(
    exp_id: int,
    data: AlumniExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exp = db.query(AlumniExperience).filter(AlumniExperience.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience record not found.")
    if exp.alumni.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    
    exp.company = data.company
    exp.job_title = data.job_title
    exp.location = data.location
    exp.start_date = data.start_date
    exp.end_date = data.end_date
    exp.is_current = data.is_current
    exp.description = data.description
    db.commit()
    db.refresh(exp)
    return {"message": "Experience updated.", "id": exp.id}

@router.delete("/alumni/experiences/{exp_id}")
def delete_alumni_experience(
    exp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exp = db.query(AlumniExperience).filter(AlumniExperience.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experience record not found.")
    if exp.alumni.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    db.delete(exp)
    db.commit()
    return {"message": "Experience deleted."}

@router.get("/students/{student_id}")
def get_student_detail(
    student_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    
    can_view_contact = (
        current_user and (
            current_user.id == student.user_id or 
            current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY]
        )
    )
    
    return {
        "id": student.id,
        "user_id": student.user_id,
        "full_name": student.full_name,
        "course": student.course,
        "batch_year": student.batch_year,
        "current_semester": student.current_semester,
        "cgpa": student.cgpa,
        "bio": student.bio,
        "avatar_url": student.avatar_url,
        "resume_url": student.resume_url if can_view_contact else None,
        "skills": [s.strip() for s in student.skills.split(",") if s.strip()] if student.skills else [],
        "skills_raw": student.skills,
        "verification_status": student.verification_status.value,
        "is_verified": student.verification_status == VerificationStatus.VERIFIED,
        "github_url": student.github_url,
        "linkedin_url": student.linkedin_url,
        "leetcode_url": student.leetcode_url,
        "portfolio_url": student.portfolio_url,
        "email": student.user.email if (can_view_contact or student.show_email) else None,
        "phone": student.phone if (can_view_contact or student.show_phone) else None
    }

@router.put("/students/profile")
@router.put("/users/profile")
@router.put("/profile")
def update_student_profile(
    data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ALUMNI:
        profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Alumni profile not found for this account.")
        for key, val in data.model_dump(exclude_unset=True).items():
            if hasattr(profile, key) and val is not None:
                setattr(profile, key, val)
        db.commit()
        db.refresh(profile)
        log_audit_event(db, "UPDATE_PROFILE", current_user.id, "AlumniProfile", profile.id, None, "Updated alumni profile")
        return {"message": "Profile updated successfully.", "profile_id": profile.id}

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        profile = StudentProfile(
            user_id=current_user.id,
            full_name=data.full_name or current_user.email.split("@")[0].capitalize(),
            course="N/A",
            enrollment_no=f"INST-{current_user.id}",
            roll_no=f"ROL-{current_user.id}",
            verification_status=VerificationStatus.VERIFIED
        )
        db.add(profile)
        db.flush()
    
    for key, val in data.model_dump(exclude_unset=True).items():
        if hasattr(profile, key) and val is not None:
            setattr(profile, key, val)
        
    db.commit()
    db.refresh(profile)
    log_audit_event(db, "UPDATE_PROFILE", current_user.id, "StudentProfile", profile.id, None, "Updated profile")
    return {"message": "Profile updated successfully."}

@router.post("/upload/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Extension validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed: {list(settings.ALLOWED_IMAGE_EXTENSIONS)}")
    
    filename = f"avatar_user_{current_user.id}_{int(os.times().elapsed)}{ext}"
    dest_path = settings.AVATARS_DIR / filename
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    url = f"/media/avatars/{filename}"
    if current_user.alumni_profile:
        current_user.alumni_profile.avatar_url = url
    elif current_user.student_profile:
        current_user.student_profile.avatar_url = url
    db.commit()
    
    return {"url": url, "message": "Avatar uploaded successfully."}

@router.post("/upload/resume")
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed: {list(settings.ALLOWED_RESUME_EXTENSIONS)}")
    
    filename = f"resume_user_{current_user.id}_{int(os.times().elapsed)}{ext}"
    dest_path = settings.RESUMES_DIR / filename
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    url = f"/media/resumes/{filename}"
    if current_user.student_profile:
        current_user.student_profile.resume_url = url
        db.commit()
        
    return {"url": url, "message": "Resume uploaded successfully."}
