from datetime import datetime, timezone
from typing import Optional, List
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import (
    User, UserRole, VerificationStatus, ProfileVisibility,
    AuthorizedCollegeRegistry, StudentProfile, AlumniProfile
)
from app.models.job import Job, JobType, JobApplication, ReferralRequest, ReferralStatus
from app.models.mentorship import MentorshipProfile, MentorshipRequest, MentorshipSession
from app.models.project import IndustryProject, ProjectProposal
from app.models.resource import TechnicalResource
from app.models.event import Event, EventRegistration
from app.models.communication import Notification, Newsletter, NewsletterSubscriber
from app.models.audit import AuditLog, UserReport
from app.schemas.user import VerificationAction
from app.schemas.communication import NewsletterCreate
from app.core.dependencies import get_current_user, require_roles
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api/admin", tags=["Administration, Analytics & Verification"])

@router.get("/dashboard")
def get_dashboard_metrics(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY])),
    db: Session = Depends(get_db)
):
    total_students = db.query(StudentProfile).count()
    total_alumni = db.query(AlumniProfile).count()
    verified_alumni = db.query(AlumniProfile).filter(AlumniProfile.verification_status == VerificationStatus.VERIFIED).count()
    pending_verifications = db.query(AlumniProfile).filter(AlumniProfile.verification_status == VerificationStatus.PENDING).count() + \
                            db.query(StudentProfile).filter(StudentProfile.verification_status == VerificationStatus.PENDING).count()
    
    bca_alumni = db.query(AlumniProfile).filter(AlumniProfile.course == "BCA").count()
    mca_alumni = db.query(AlumniProfile).filter(AlumniProfile.course == "MCA").count()
    
    active_mentors = db.query(AlumniProfile).filter(AlumniProfile.is_mentor == True).count()
    jobs_posted = db.query(Job).filter(Job.job_type == JobType.FULL_TIME).count()
    internships_posted = db.query(Job).filter(Job.job_type == JobType.INTERNSHIP).count()
    total_referrals = db.query(ReferralRequest).count()
    active_projects = db.query(IndustryProject).count()
    upcoming_events = db.query(Event).count()
    resources_count = db.query(TechnicalResource).count()
    
    # 1. Batch distribution
    batches = db.query(AlumniProfile.batch_year, func.count(AlumniProfile.id)).group_by(AlumniProfile.batch_year).order_by(AlumniProfile.batch_year.asc()).all()
    batch_chart = [{"batch": str(b[0]), "count": b[1]} for b in batches]
    
    # 2. Company distribution
    companies = db.query(AlumniProfile.current_company, func.count(AlumniProfile.id)).filter(AlumniProfile.current_company.isnot(None)).group_by(AlumniProfile.current_company).order_by(func.count(AlumniProfile.id).desc()).limit(8).all()
    company_chart = [{"company": c[0], "count": c[1]} for c in companies if c[0]]
    
    # 3. Technology / Skills distribution
    all_skills_rows = db.query(AlumniProfile.skills).all()
    skill_counter = Counter()
    for row in all_skills_rows:
        if row[0]:
            for s in row[0].split(","):
                cleaned = s.strip()
                if cleaned:
                    skill_counter[cleaned] += 1
    tech_chart = [{"technology": t, "count": count} for t, count in skill_counter.most_common(10)]
    
    # 4. Referral status breakdown
    ref_statuses = db.query(ReferralRequest.status, func.count(ReferralRequest.id)).group_by(ReferralRequest.status).all()
    referral_chart = [{"status": r[0].value if hasattr(r[0], 'value') else str(r[0]), "count": r[1]} for r in ref_statuses]

    return {
        "metrics": {
            "total_students": total_students,
            "total_alumni": total_alumni,
            "verified_alumni": verified_alumni,
            "pending_verifications": pending_verifications,
            "bca_alumni": bca_alumni,
            "mca_alumni": mca_alumni,
            "active_mentors": active_mentors,
            "jobs_posted": jobs_posted,
            "internships_posted": internships_posted,
            "total_referrals": total_referrals,
            "active_projects": active_projects,
            "upcoming_events": upcoming_events,
            "resources_count": resources_count,
            "monthly_active_users": total_students + total_alumni + 12
        },
        "charts": {
            "batch_distribution": batch_chart,
            "company_distribution": company_chart,
            "technology_distribution": tech_chart,
            "referral_distribution": referral_chart
        }
    }

# ================= VERIFICATION QUEUE =================

@router.get("/verifications")
def get_verification_queue(
    user_type: Optional[str] = Query(None, description="alumni or student"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY])),
    db: Session = Depends(get_db)
):
    results = []
    
    # Alumni pending verification
    if not user_type or user_type == "alumni":
        alumni_pending = db.query(AlumniProfile).filter(AlumniProfile.verification_status == VerificationStatus.PENDING).all()
        for a in alumni_pending:
            results.append({
                "profile_id": a.id,
                "user_id": a.user_id,
                "type": "alumni",
                "full_name": a.full_name,
                "email": a.user.email if a.user else "",
                "enrollment_no": a.enrollment_no,
                "roll_no": a.roll_no,
                "course": a.course,
                "batch_year": a.batch_year,
                "graduation_year": a.graduation_year,
                "current_company": a.current_company,
                "current_job_title": a.current_job_title,
                "status": a.verification_status.value,
                "created_at": a.created_at.isoformat()
            })
            
    # Students pending verification
    if not user_type or user_type == "student":
        students_pending = db.query(StudentProfile).filter(StudentProfile.verification_status == VerificationStatus.PENDING).all()
        for s in students_pending:
            results.append({
                "profile_id": s.id,
                "user_id": s.user_id,
                "type": "student",
                "full_name": s.full_name,
                "email": s.user.email if s.user else "",
                "enrollment_no": s.enrollment_no,
                "roll_no": s.roll_no,
                "course": s.course,
                "batch_year": s.batch_year,
                "current_semester": s.current_semester,
                "status": s.verification_status.value,
                "created_at": s.user.created_at.isoformat() if s.user else ""
            })
            
    return results

@router.put("/verifications/{profile_id}")
def update_verification_status(
    profile_id: int,
    user_type: str = Query("alumni"),
    action: VerificationAction = ...,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY])),
    db: Session = Depends(get_db)
):
    target_user_id = None
    target_name = ""
    
    if user_type == "alumni":
        prof = db.query(AlumniProfile).filter(AlumniProfile.id == profile_id).first()
        if not prof:
            raise HTTPException(status_code=404, detail="Alumni profile not found.")
        prof.verification_status = action.status
        prof.verification_notes = action.notes or f"Processed by {current_user.email}"
        target_user_id = prof.user_id
        target_name = prof.full_name
        # Update user.is_verified flag
        if prof.user:
            prof.user.is_verified = (action.status == VerificationStatus.VERIFIED)
    else:
        prof = db.query(StudentProfile).filter(StudentProfile.id == profile_id).first()
        if not prof:
            raise HTTPException(status_code=404, detail="Student profile not found.")
        prof.verification_status = action.status
        prof.verification_notes = action.notes or f"Processed by {current_user.email}"
        target_user_id = prof.user_id
        target_name = prof.full_name
        if prof.user:
            prof.user.is_verified = (action.status == VerificationStatus.VERIFIED)

    # In-app notification to the user
    status_label = action.status.value.title()
    notif = Notification(
        user_id=target_user_id,
        title=f"CMS Account Verification: {status_label}",
        message=f"Your institutional verification was updated to {status_label}. {action.notes or ''}",
        notification_type="verification",
        link="/profile"
    )
    db.add(notif)
    db.commit()
    
    log_audit_event(
        db, "VERIFY_USER", current_user.id, "User", target_user_id, None,
        f"Verification status changed to {action.status.value} for {target_name}"
    )
    return {"message": f"Verification status updated to {action.status.value}."}

# ================= USER MANAGEMENT =================

@router.get("/users")
def get_users_list(
    role: Optional[UserRole] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if q:
        search_fmt = f"%{q.strip()}%"
        query = query.filter(User.email.ilike(search_fmt))
        
    total_count = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(User.id.desc()).offset(offset).limit(page_size).all()
    
    results = []
    for u in users:
        full_name = "User"
        course = ""
        batch = ""
        ver_status = "verified" if u.is_verified else "pending"
        if u.role == UserRole.ALUMNI and u.alumni_profile:
            full_name = u.alumni_profile.full_name
            course = u.alumni_profile.course
            batch = str(u.alumni_profile.batch_year)
            ver_status = u.alumni_profile.verification_status.value
        elif u.student_profile:
            full_name = u.student_profile.full_name
            course = u.student_profile.course
            batch = str(u.student_profile.batch_year)
            ver_status = u.student_profile.verification_status.value
            
        results.append({
            "id": u.id,
            "email": u.email,
            "role": u.role.value,
            "full_name": full_name,
            "course": course,
            "batch": batch,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "verification_status": ver_status,
            "created_at": u.created_at.isoformat()
        })
        
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "items": results
    }

@router.put("/users/{user_id}/status")
def toggle_user_active_status(
    user_id: int,
    is_active: bool = Query(...),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot alter Super Admin status.")
        
    user.is_active = is_active
    db.commit()
    log_audit_event(db, "TOGGLE_USER_STATUS", current_user.id, "User", user.id, None, f"Set is_active={is_active}")
    return {"message": f"User status set to {'active' if is_active else 'suspended'}."}

@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    new_role: UserRole = Query(...),
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    old_role = user.role.value
    user.role = new_role
    db.commit()
    log_audit_event(db, "CHANGE_USER_ROLE", current_user.id, "User", user.id, None, f"Changed role from {old_role} to {new_role.value}")
    return {"message": f"Role updated to {new_role.value}."}

# ================= AUDIT LOGS =================

@router.get("/audit-logs")
def get_audit_logs(
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action.strip()}%"))
        
    total_count = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()
    
    results = []
    for l in logs:
        user_email = l.user.email if l.user else "System/Guest"
        results.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_email": user_email,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "ip_address": l.ip_address,
            "details": l.details,
            "created_at": l.created_at.isoformat()
        })
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "items": results
    }

# ================= NEWSLETTERS =================

@router.get("/newsletters")
def get_newsletters(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY])),
    db: Session = Depends(get_db)
):
    news = db.query(Newsletter).order_by(Newsletter.created_at.desc()).all()
    sub_count = db.query(NewsletterSubscriber).count()
    return {
        "subscriber_count": sub_count,
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "content_html": n.content_html,
                "is_sent": n.is_sent,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "created_at": n.created_at.isoformat()
            } for n in news
        ]
    }

@router.post("/newsletters")
def create_newsletter(
    data: NewsletterCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    nl = Newsletter(
        title=data.title,
        content_html=data.content_html,
        sent_by_id=current_user.id,
        scheduled_for=data.scheduled_for,
        is_sent=False
    )
    db.add(nl)
    db.commit()
    db.refresh(nl)
    return {"message": "Newsletter created.", "id": nl.id}

@router.post("/newsletters/{newsletter_id}/send")
def send_newsletter(
    newsletter_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    nl = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found.")
        
    nl.is_sent = True
    nl.sent_at = datetime.now(timezone.utc)
    
    # Broadcast in-app notification to all users
    users = db.query(User).filter(User.is_active == True).all()
    for u in users:
        notif = Notification(
            user_id=u.id,
            title=f"CMS Kanpur Monthly Newsletter: {nl.title}",
            message=f"Read the latest updates, alumni highlights, and technical placements from CMS Kanpur.",
            notification_type="system",
            link="/newsletters"
        )
        db.add(notif)
    db.commit()
    
    log_audit_event(db, "SEND_NEWSLETTER", current_user.id, "Newsletter", nl.id, None, f"Dispatched newsletter: {nl.title} to {len(users)} users")
    return {"message": f"Newsletter broadcasted to {len(users)} members successfully!"}
