from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.user import User, UserRole
from app.models.job import (
    Job, JobType, LocationType, ApplicationStatus,
    ReferralStatus, JobApplication, ReferralRequest, SavedJob
)
from app.models.communication import Notification
from app.schemas.job import (
    JobCreate, JobUpdate, JobApplicationCreate,
    ApplicationStatusUpdate, ReferralRequestCreate, ReferralRequestUpdate
)
from app.core.dependencies import get_current_user, get_optional_current_user, require_roles
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api", tags=["Jobs, Internships & Referrals"])

@router.get("/jobs")
def get_jobs(
    q: Optional[str] = Query(None, description="Search by title, company, skills"),
    job_type: Optional[JobType] = Query(None),
    location_type: Optional[LocationType] = Query(None),
    referral_only: Optional[bool] = Query(None),
    skills: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Job).filter(Job.is_active == True)
    
    if q:
        search_fmt = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_fmt),
                Job.company.ilike(search_fmt),
                Job.required_skills.ilike(search_fmt),
                Job.location.ilike(search_fmt)
            )
        )
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if location_type:
        query = query.filter(Job.location_type == location_type)
    if referral_only:
        query = query.filter(Job.is_referral_available == True)
    if skills:
        query = query.filter(Job.required_skills.ilike(f"%{skills.strip()}%"))
        
    total_count = query.count()
    offset = (page - 1) * page_size
    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size).all()
    
    saved_job_ids = set()
    if current_user:
        saved_job_ids = {s.job_id for s in db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()}
        
    results = []
    for job in jobs:
        poster_name = "CMS Alumni"
        if job.poster and job.poster.alumni_profile:
            poster_name = job.poster.alumni_profile.full_name
        elif job.poster and job.poster.student_profile:
            poster_name = job.poster.student_profile.full_name
            
        results.append({
            "id": job.id,
            "poster_id": job.poster_id,
            "poster_name": poster_name,
            "title": job.title,
            "company": job.company,
            "job_type": job.job_type.value,
            "location_type": job.location_type.value,
            "location": job.location,
            "experience_required": job.experience_required,
            "salary_range": job.salary_range,
            "required_skills": [s.strip() for s in job.required_skills.split(",") if s.strip()],
            "required_skills_raw": job.required_skills,
            "description": job.description,
            "external_apply_url": job.external_apply_url,
            "deadline": job.deadline,
            "is_referral_available": job.is_referral_available,
            "is_active": job.is_active,
            "created_at": job.created_at.isoformat(),
            "applications_count": len(job.applications),
            "is_saved": job.id in saved_job_ids
        })
        
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
        "items": results
    }

@router.get("/jobs/{job_id}")
def get_job_detail(
    job_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    is_saved = False
    has_applied = False
    if current_user:
        is_saved = db.query(SavedJob).filter(SavedJob.user_id == current_user.id, SavedJob.job_id == job.id).first() is not None
        has_applied = db.query(JobApplication).filter(JobApplication.applicant_id == current_user.id, JobApplication.job_id == job.id).first() is not None

    poster_name = "CMS Alumni"
    poster_company = ""
    if job.poster and job.poster.alumni_profile:
        poster_name = job.poster.alumni_profile.full_name
        poster_company = job.poster.alumni_profile.current_company

    return {
        "id": job.id,
        "poster_id": job.poster_id,
        "poster_name": poster_name,
        "poster_company": poster_company,
        "title": job.title,
        "company": job.company,
        "job_type": job.job_type.value,
        "location_type": job.location_type.value,
        "location": job.location,
        "experience_required": job.experience_required,
        "salary_range": job.salary_range,
        "required_skills": [s.strip() for s in job.required_skills.split(",") if s.strip()],
        "required_skills_raw": job.required_skills,
        "description": job.description,
        "external_apply_url": job.external_apply_url,
        "deadline": job.deadline,
        "is_referral_available": job.is_referral_available,
        "created_at": job.created_at.isoformat(),
        "is_saved": is_saved,
        "has_applied": has_applied,
        "applications_count": len(job.applications)
    }

@router.post("/jobs")
def create_job(
    data: JobCreate,
    current_user: User = Depends(require_roles([UserRole.ALUMNI, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY])),
    db: Session = Depends(get_db)
):
    job = Job(
        poster_id=current_user.id,
        title=data.title,
        company=data.company,
        job_type=data.job_type,
        location_type=data.location_type,
        location=data.location,
        experience_required=data.experience_required,
        salary_range=data.salary_range,
        required_skills=data.required_skills,
        description=data.description,
        external_apply_url=data.external_apply_url,
        deadline=data.deadline,
        is_referral_available=data.is_referral_available,
        is_active=True
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    log_audit_event(db, "CREATE_JOB", current_user.id, "Job", job.id, None, f"Posted {data.job_type.value}: {data.title} at {data.company}")
    return {"message": "Job / opportunity posted successfully.", "job_id": job.id}

@router.put("/jobs/{job_id}")
def update_job(
    job_id: int,
    data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.poster_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(job, key, val)
        
    db.commit()
    return {"message": "Job updated successfully."}

@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.poster_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    
    db.delete(job)
    db.commit()
    log_audit_event(db, "DELETE_JOB", current_user.id, "Job", job_id, None, "Job removed")
    return {"message": "Job deleted."}

@router.post("/jobs/{job_id}/apply")
def apply_to_job(
    job_id: int,
    data: JobApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting is no longer active.")
    
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.applicant_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied for this opening.")
    
    resume = data.resume_url
    if not resume and current_user.student_profile and current_user.student_profile.resume_url:
        resume = current_user.student_profile.resume_url
        
    app = JobApplication(
        job_id=job.id,
        applicant_id=current_user.id,
        resume_url=resume,
        cover_note=data.cover_note,
        status=ApplicationStatus.APPLIED
    )
    db.add(app)
    
    # Notify job poster
    applicant_name = current_user.student_profile.full_name if current_user.student_profile else current_user.email
    notif = Notification(
        user_id=job.poster_id,
        title="New Job Application Received",
        message=f"{applicant_name} applied for your opening: '{job.title}' at {job.company}.",
        notification_type="job",
        link=f"/jobs/{job.id}"
    )
    db.add(notif)
    db.commit()
    
    log_audit_event(db, "APPLY_JOB", current_user.id, "JobApplication", app.id, None, f"Applied to job {job.id}")
    return {"message": "Application submitted successfully!", "application_id": app.id}

@router.get("/jobs/{job_id}/applications")
def get_job_applications(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.poster_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    
    apps = db.query(JobApplication).filter(JobApplication.job_id == job_id).order_by(JobApplication.applied_at.desc()).all()
    results = []
    for a in apps:
        name = "Student Applicant"
        course = "BCA"
        batch = 2023
        skills = ""
        github = ""
        if a.applicant and a.applicant.student_profile:
            p = a.applicant.student_profile
            name = p.full_name
            course = p.course
            batch = p.batch_year
            skills = p.skills
            github = p.github_url
        results.append({
            "id": a.id,
            "applicant_id": a.applicant_id,
            "applicant_name": name,
            "applicant_course": f"{course} ({batch})",
            "applicant_skills": skills,
            "github_url": github,
            "resume_url": a.resume_url,
            "cover_note": a.cover_note,
            "status": a.status.value,
            "applied_at": a.applied_at.isoformat()
        })
    return results

@router.put("/jobs/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.job.poster_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    
    app.status = data.status
    # Notify student
    notif = Notification(
        user_id=app.applicant_id,
        title="Application Status Updated",
        message=f"Your application status for '{app.job.title}' at {app.job.company} was updated to: {data.status.value.replace('_', ' ').title()}.",
        notification_type="job",
        link=f"/jobs/{app.job_id}"
    )
    db.add(notif)
    db.commit()
    return {"message": "Application status updated successfully."}

@router.post("/jobs/{job_id}/save")
def toggle_save_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(SavedJob).filter(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"saved": False, "message": "Job removed from saved list."}
    else:
        new_save = SavedJob(user_id=current_user.id, job_id=job_id)
        db.add(new_save)
        db.commit()
        return {"saved": True, "message": "Job saved."}

# ================= REFERRAL WORKFLOW =================

@router.post("/referrals/request")
def request_referral(
    data: ReferralRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alumni_user = db.query(User).filter(User.id == data.alumni_id).first()
    if not alumni_user:
        alumni_prof = db.query(AlumniProfile).filter(AlumniProfile.id == data.alumni_id).first()
        if alumni_prof:
            alumni_user = alumni_prof.user
            data.alumni_id = alumni_user.id
    if not alumni_user or alumni_user.role != UserRole.ALUMNI:
        raise HTTPException(status_code=404, detail="Alumni not found.")
    
    resume = data.resume_url
    if not resume and current_user.student_profile and current_user.student_profile.resume_url:
        resume = current_user.student_profile.resume_url

    req = ReferralRequest(
        alumni_id=data.alumni_id,
        student_id=current_user.id,
        job_id=data.job_id,
        target_company=data.target_company,
        target_role=data.target_role,
        resume_url=resume,
        note=data.note,
        status=ReferralStatus.REQUESTED
    )
    db.add(req)
    
    # Notify alumni
    student_name = current_user.student_profile.full_name if current_user.student_profile else "A CMS Kanpur student"
    notif = Notification(
        user_id=data.alumni_id,
        title="New Alumni Referral Request",
        message=f"{student_name} requested an internal referral for '{data.target_role}' at {data.target_company}.",
        notification_type="referral",
        link="/referrals"
    )
    db.add(notif)
    db.commit()
    
    log_audit_event(db, "REQUEST_REFERRAL", current_user.id, "ReferralRequest", req.id, None, f"Referral requested from user {data.alumni_id}")
    return {"message": "Referral request submitted successfully!", "referral_id": req.id}

@router.get("/referrals/my-requests")
def get_my_referral_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requests = db.query(ReferralRequest).filter(ReferralRequest.student_id == current_user.id).order_by(ReferralRequest.created_at.desc()).all()
    results = []
    for r in requests:
        alumni_name = "CMS Alumnus"
        alumni_company = r.target_company
        if r.alumni and r.alumni.alumni_profile:
            alumni_name = r.alumni.alumni_profile.full_name
            alumni_company = r.alumni.alumni_profile.current_company
        results.append({
            "id": r.id,
            "alumni_id": r.alumni_id,
            "alumni_name": alumni_name,
            "alumni_company": alumni_company,
            "target_company": r.target_company,
            "target_role": r.target_role,
            "resume_url": r.resume_url,
            "note": r.note,
            "status": r.status.value,
            "feedback": r.feedback,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat()
        })
    return results

@router.get("/referrals/received")
def get_received_referral_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requests = db.query(ReferralRequest).filter(ReferralRequest.alumni_id == current_user.id).order_by(ReferralRequest.created_at.desc()).all()
    results = []
    for r in requests:
        student_name = "Student"
        student_course = "BCA"
        batch = 2023
        skills = ""
        github = ""
        linkedin = ""
        if r.student and r.student.student_profile:
            p = r.student.student_profile
            student_name = p.full_name
            student_course = p.course
            batch = p.batch_year
            skills = p.skills
            github = p.github_url
            linkedin = p.linkedin_url
        results.append({
            "id": r.id,
            "student_id": r.student_id,
            "student_name": student_name,
            "student_course": f"{student_course} ({batch})",
            "skills": skills,
            "github_url": github,
            "linkedin_url": linkedin,
            "target_company": r.target_company,
            "target_role": r.target_role,
            "resume_url": r.resume_url,
            "note": r.note,
            "status": r.status.value,
            "feedback": r.feedback,
            "created_at": r.created_at.isoformat()
        })
    return results

@router.put("/referrals/{request_id}/status")
def update_referral_status(
    request_id: int,
    data: ReferralRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(ReferralRequest).filter(ReferralRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Referral request not found.")
    if req.alumni_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    
    req.status = data.status
    if data.feedback:
        req.feedback = data.feedback
        
    # Notify student
    status_label = data.status.value.replace('_', ' ').title()
    notif = Notification(
        user_id=req.student_id,
        title="Referral Request Update",
        message=f"Your referral request for '{req.target_role}' at {req.target_company} status changed to: {status_label}.",
        notification_type="referral",
        link="/referrals"
    )
    db.add(notif)
    db.commit()
    
    log_audit_event(db, "UPDATE_REFERRAL_STATUS", current_user.id, "ReferralRequest", req.id, None, f"Referral status changed to {data.status.value}")
    return {"message": "Referral status updated successfully."}
