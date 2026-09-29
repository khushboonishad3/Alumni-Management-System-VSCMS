from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.mentorship import (
    MentorshipProfile, MentorshipRequest, MentorshipSession,
    MockInterview, ResumeReview, MentorshipStatus, SessionStatus,
    InterviewType, ReviewStatus
)
from app.models.communication import Notification
from app.schemas.mentorship import (
    MentorshipProfileUpdate, MentorshipRequestCreate,
    MentorshipRequestUpdate, MentorshipSessionCreate,
    MockInterviewCreate, ResumeReviewCreate
)
from app.core.dependencies import get_current_user
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api/mentorship", tags=["Mentorship, Mock Interviews & Resume Reviews"])

@router.get("/mentors")
def list_mentors(
    topic: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List verified alumni available for 1-on-1 mentorship."""
    query = db.query(MentorshipProfile).join(MentorshipProfile.alumni).filter(MentorshipProfile.is_active == True)
    
    if topic:
        query = query.filter(MentorshipProfile.topics.ilike(f"%{topic.strip()}%"))
        
    profiles = query.all()
    results = []
    for p in profiles:
        alumni = p.alumni
        if not alumni:
            continue
        if company and company.lower() not in (alumni.current_company or "").lower():
            continue
            
        results.append({
            "id": p.id,
            "alumni_id": alumni.user_id,
            "alumni_profile_id": alumni.id,
            "full_name": alumni.full_name,
            "course": alumni.course,
            "batch_year": alumni.batch_year,
            "graduation_year": alumni.graduation_year,
            "company": alumni.current_company,
            "job_title": alumni.current_job_title,
            "avatar_url": alumni.avatar_url,
            "topics": [t.strip() for t in p.topics.split(",") if t.strip()],
            "bio": p.bio or alumni.bio,
            "max_mentees": p.max_mentees,
            "meeting_format": p.meeting_format,
            "availability_details": p.availability_details,
            "linkedin_url": alumni.linkedin_url,
            "github_url": alumni.github_url
        })
    return results

@router.get("/profile")
def get_my_mentorship_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.alumni_profile:
        raise HTTPException(status_code=400, detail="Only alumni have a mentorship profile.")
    
    prof = db.query(MentorshipProfile).filter(MentorshipProfile.alumni_id == current_user.alumni_profile.id).first()
    if not prof:
        prof = MentorshipProfile(alumni_id=current_user.alumni_profile.id)
        db.add(prof)
        db.commit()
        db.refresh(prof)
        
    return {
        "id": prof.id,
        "topics": prof.topics,
        "bio": prof.bio,
        "max_mentees": prof.max_mentees,
        "meeting_format": prof.meeting_format,
        "availability_details": prof.availability_details,
        "is_active": prof.is_active
    }

@router.put("/profile")
def update_mentorship_profile(
    data: MentorshipProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.alumni_profile:
        raise HTTPException(status_code=400, detail="Only alumni can manage a mentorship profile.")
    
    prof = db.query(MentorshipProfile).filter(MentorshipProfile.alumni_id == current_user.alumni_profile.id).first()
    if not prof:
        prof = MentorshipProfile(alumni_id=current_user.alumni_profile.id)
        db.add(prof)
        
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(prof, key, val)
        
    db.commit()
    return {"message": "Mentorship settings updated."}

@router.post("/requests")
def send_mentorship_request(
    data: MentorshipRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    mentor = db.query(User).filter(User.id == data.mentor_id).first()
    if not mentor:
        alumni_prof = db.query(AlumniProfile).filter(AlumniProfile.id == data.mentor_id).first()
        if alumni_prof:
            mentor = alumni_prof.user
            data.mentor_id = mentor.id
    if not mentor or mentor.role != UserRole.ALUMNI:
        raise HTTPException(status_code=404, detail="Alumni mentor not found.")
    
    req = MentorshipRequest(
        mentor_id=data.mentor_id,
        mentee_id=current_user.id,
        topic=data.topic,
        message=data.message,
        status=MentorshipStatus.REQUESTED
    )
    db.add(req)
    
    mentee_name = current_user.student_profile.full_name if current_user.student_profile else "A CMS student"
    notif = Notification(
        user_id=data.mentor_id,
        title="New Mentorship Request",
        message=f"{mentee_name} sent you a mentorship request for '{data.topic}'.",
        notification_type="mentorship",
        link="/mentorship"
    )
    db.add(notif)
    db.commit()
    
    log_audit_event(db, "REQUEST_MENTORSHIP", current_user.id, "MentorshipRequest", req.id, None, f"Requested mentorship from {data.mentor_id}")
    return {"message": "Mentorship request sent successfully!", "request_id": req.id}

@router.get("/requests")
def get_mentorship_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ALUMNI:
        requests = db.query(MentorshipRequest).filter(MentorshipRequest.mentor_id == current_user.id).order_by(MentorshipRequest.created_at.desc()).all()
    else:
        requests = db.query(MentorshipRequest).filter(MentorshipRequest.mentee_id == current_user.id).order_by(MentorshipRequest.created_at.desc()).all()
        
    results = []
    for r in requests:
        other_name = "User"
        other_detail = ""
        if current_user.role == UserRole.ALUMNI:
            if r.mentee and r.mentee.student_profile:
                other_name = r.mentee.student_profile.full_name
                other_detail = f"{r.mentee.student_profile.course} ({r.mentee.student_profile.batch_year})"
        else:
            if r.mentor and r.mentor.alumni_profile:
                other_name = r.mentor.alumni_profile.full_name
                other_detail = f"{r.mentor.alumni_profile.current_job_title} at {r.mentor.alumni_profile.current_company}"
                
        results.append({
            "id": r.id,
            "mentor_id": r.mentor_id,
            "mentee_id": r.mentee_id,
            "other_name": other_name,
            "other_detail": other_detail,
            "topic": r.topic,
            "message": r.message,
            "status": r.status.value,
            "created_at": r.created_at.isoformat(),
            "sessions": [
                {
                    "id": s.id,
                    "scheduled_at": s.scheduled_at.isoformat(),
                    "duration_minutes": s.duration_minutes,
                    "meeting_link": s.meeting_link,
                    "agenda": s.agenda,
                    "status": s.status.value,
                    "rating": s.mentee_rating
                } for s in r.sessions
            ]
        })
    return results

@router.put("/requests/{request_id}/status")
def update_mentorship_request_status(
    request_id: int,
    data: MentorshipRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(MentorshipRequest).filter(MentorshipRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    if req.mentor_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
        
    req.status = data.status
    
    # Notify mentee
    notif = Notification(
        user_id=req.mentee_id,
        title="Mentorship Request Updated",
        message=f"Your mentorship request for '{req.topic}' was marked as: {data.status.value.title()}.",
        notification_type="mentorship",
        link="/mentorship"
    )
    db.add(notif)
    db.commit()
    return {"message": "Status updated."}

@router.post("/sessions")
def schedule_session(
    request_id: int,
    data: MentorshipSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(MentorshipRequest).filter(MentorshipRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Mentorship relationship not found.")
    if req.mentor_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only the mentor can schedule sessions.")
        
    session = MentorshipSession(
        request_id=req.id,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        meeting_link=data.meeting_link,
        agenda=data.agenda,
        status=SessionStatus.SCHEDULED
    )
    db.add(session)
    req.status = MentorshipStatus.ACTIVE
    
    # Notify mentee
    notif = Notification(
        user_id=req.mentee_id,
        title="Mentorship Session Scheduled",
        message=f"A session on '{req.topic}' has been scheduled for {data.scheduled_at.strftime('%b %d, %Y %I:%M %p')}.",
        notification_type="mentorship",
        link=data.meeting_link or "/mentorship"
    )
    db.add(notif)
    db.commit()
    
    return {"message": "Session scheduled successfully!", "session_id": session.id}

# ================= MOCK INTERVIEW SERVICE =================

@router.post("/mock-interviews")
def request_mock_interview(
    data: MockInterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interviewer = db.query(User).filter(User.id == data.interviewer_id).first()
    if not interviewer or interviewer.role != UserRole.ALUMNI:
        raise HTTPException(status_code=404, detail="Alumni interviewer not found.")
        
    mock = MockInterview(
        interviewer_id=data.interviewer_id,
        interviewee_id=current_user.id,
        interview_type=data.interview_type,
        status="requested"
    )
    db.add(mock)
    
    applicant_name = current_user.student_profile.full_name if current_user.student_profile else "A CMS student"
    notif = Notification(
        user_id=data.interviewer_id,
        title="Mock Interview Request",
        message=f"{applicant_name} booked a {data.interview_type.value.replace('_', ' ').title()} Mock Interview with you.",
        notification_type="mentorship",
        link="/mentorship"
    )
    db.add(notif)
    db.commit()
    return {"message": "Mock interview requested successfully!", "id": mock.id}

@router.get("/mock-interviews")
def get_mock_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ALUMNI:
        interviews = db.query(MockInterview).filter(MockInterview.interviewer_id == current_user.id).order_by(MockInterview.created_at.desc()).all()
    else:
        interviews = db.query(MockInterview).filter(MockInterview.interviewee_id == current_user.id).order_by(MockInterview.created_at.desc()).all()
        
    results = []
    for m in interviews:
        other_name = "CMS Member"
        if current_user.role == UserRole.ALUMNI:
            if m.interviewee and m.interviewee.student_profile:
                other_name = m.interviewee.student_profile.full_name
        else:
            if m.interviewer and m.interviewer.alumni_profile:
                other_name = m.interviewer.alumni_profile.full_name
                
        results.append({
            "id": m.id,
            "other_name": other_name,
            "interview_type": m.interview_type.value,
            "status": m.status,
            "meeting_link": m.meeting_link,
            "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
            "feedback": m.feedback,
            "rating": m.rating,
            "created_at": m.created_at.isoformat()
        })
    return results

# ================= RESUME REVIEW SERVICE =================

@router.post("/resume-reviews")
def request_resume_review(
    data: ResumeReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reviewer = db.query(User).filter(User.id == data.reviewer_id).first()
    if not reviewer or reviewer.role != UserRole.ALUMNI:
        raise HTTPException(status_code=404, detail="Alumni reviewer not found.")
        
    rev = ResumeReview(
        reviewer_id=data.reviewer_id,
        student_id=current_user.id,
        resume_url=data.resume_url,
        target_roles=data.target_roles,
        status=ReviewStatus.REQUESTED
    )
    db.add(rev)
    
    student_name = current_user.student_profile.full_name if current_user.student_profile else "A CMS student"
    notif = Notification(
        user_id=data.reviewer_id,
        title="Resume Review Request",
        message=f"{student_name} requested your review on their resume targeting: {data.target_roles}.",
        notification_type="mentorship",
        link="/mentorship"
    )
    db.add(notif)
    db.commit()
    return {"message": "Resume submitted for review!", "id": rev.id}

@router.get("/resume-reviews")
def get_resume_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ALUMNI:
        reviews = db.query(ResumeReview).filter(ResumeReview.reviewer_id == current_user.id).order_by(ResumeReview.created_at.desc()).all()
    else:
        reviews = db.query(ResumeReview).filter(ResumeReview.student_id == current_user.id).order_by(ResumeReview.created_at.desc()).all()
        
    results = []
    for r in reviews:
        student_name = r.student.student_profile.full_name if (r.student and r.student.student_profile) else "Student"
        reviewer_name = r.reviewer.alumni_profile.full_name if (r.reviewer and r.reviewer.alumni_profile) else "Alumni Reviewer"
        results.append({
            "id": r.id,
            "student_name": student_name,
            "reviewer_name": reviewer_name,
            "resume_url": r.resume_url,
            "target_roles": r.target_roles,
            "status": r.status.value,
            "review_comments": r.review_comments,
            "suggestions": r.suggestions,
            "created_at": r.created_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None
        })
    return results

@router.put("/resume-reviews/{review_id}")
def update_resume_review(
    review_id: int,
    comments: str = Query(...),
    suggestions: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = db.query(ResumeReview).filter(ResumeReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review request not found.")
    if review.reviewer_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden.")
        
    review.review_comments = comments
    review.suggestions = suggestions
    review.status = ReviewStatus.COMPLETED
    review.completed_at = datetime.now(timezone.utc)
    
    # Notify student
    notif = Notification(
        user_id=review.student_id,
        title="Resume Review Completed!",
        message=f"Alumni feedback has been published for your resume review request.",
        notification_type="mentorship",
        link="/mentorship"
    )
    db.add(notif)
    db.commit()
    return {"message": "Resume review saved and delivered to student."}
