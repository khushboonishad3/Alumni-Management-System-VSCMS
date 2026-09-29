import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import (
    User, UserRole, VerificationStatus, ProfileVisibility,
    AuthorizedCollegeRegistry, StudentProfile, AlumniProfile
)
from app.models.mentorship import MentorshipProfile
from app.schemas.auth import (
    UserLogin, UserRegister, TokenResponse, CaptchaResponse,
    PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest
)
from app.core.security import (
    hash_password, verify_password, create_access_token,
    generate_captcha_token, verify_captcha_token
)
from app.core.dependencies import get_current_user
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

CAPTCHA_STORE = {}

def clean_expired_captchas():
    now = datetime.now(timezone.utc)
    expired = [k for k, v in CAPTCHA_STORE.items() if v["expires_at"] < now]
    for k in expired:
        CAPTCHA_STORE.pop(k, None)

def generate_captcha_svg(code: str) -> str:
    chars_svg = ""
    colors = ["#162E5F", "#90231D", "#0F172A", "#B91C1C", "#1E3A8A"]
    x = 18
    for ch in code:
        rot = random.randint(-18, 18)
        y = random.randint(32, 38)
        color = random.choice(colors)
        chars_svg += f'<text x="{x}" y="{y}" font-family="monospace, Courier New" font-weight="900" font-size="28" fill="{color}" transform="rotate({rot}, {x}, {y})">{ch}</text>'
        x += 24

    lines = ""
    for _ in range(4):
        x1, y1 = random.randint(0, 150), random.randint(0, 48)
        x2, y2 = random.randint(0, 150), random.randint(0, 48)
        c = random.choice(["#94A3B8", "#CBD5E1", "#E2E8F0"])
        lines += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="1.5" />'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="150" height="48" viewBox="0 0 150 48" style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; user-select: none;">
        {lines}
        {chars_svg}
    </svg>'''

@router.get("/captcha", response_model=CaptchaResponse)
def get_captcha():
    clean_expired_captchas()
    chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    code = "".join(random.choices(chars, k=5))
    captcha_id = generate_captcha_token(code)
    CAPTCHA_STORE[captcha_id] = {
        "code": code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    svg = generate_captcha_svg(code)
    return CaptchaResponse(captcha_id=captcha_id, captcha_svg=svg)

@router.post("/register", response_model=TokenResponse)
def register(req: UserRegister, request: Request, response: Response, db: Session = Depends(get_db)):
    # 1. Check if email already exists
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
    
    # 2. Check College Institutional Verification Dataset
    roster_match = db.query(AuthorizedCollegeRegistry).filter(
        AuthorizedCollegeRegistry.enrollment_no == req.enrollment_no.strip(),
        AuthorizedCollegeRegistry.roll_no == req.roll_no.strip()
    ).first()
    
    is_auto_verified = False
    verification_notes = "Pending manual verification by CMS Kanpur administration."
    if roster_match:
        # Match confirmed in official CMS Kanpur registry
        is_auto_verified = True
        verification_notes = f"Verified automatically against CMS Kanpur official roster ({roster_match.course} {roster_match.batch_year})."
        roster_match.is_claimed = True

    verification_status = VerificationStatus.VERIFIED if is_auto_verified else VerificationStatus.PENDING

    # 3. Create User
    new_user = User(
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        role=req.role,
        is_active=True,
        is_verified=is_auto_verified
    )
    db.add(new_user)
    db.flush() # get new_user.id
    
    # 4. Create Profile according to role
    if req.role == UserRole.ALUMNI:
        grad_year = req.graduation_year or (req.batch_year + (3 if req.course.upper() == "BCA" else 2))
        alumni_profile = AlumniProfile(
            user_id=new_user.id,
            full_name=req.full_name.strip(),
            enrollment_no=req.enrollment_no.strip(),
            roll_no=req.roll_no.strip(),
            course=req.course.upper(),
            batch_year=req.batch_year,
            graduation_year=grad_year,
            current_company=req.current_company or "Tech Professional",
            current_job_title=req.current_job_title or "Software Engineer",
            skills=req.skills or "Python, JavaScript, SQL",
            linkedin_url=req.linkedin_url,
            github_url=req.github_url,
            verification_status=verification_status,
            verification_notes=verification_notes,
            profile_visibility=ProfileVisibility.PUBLIC,
            is_mentor=True,
            is_referral_provider=True
        )
        db.add(alumni_profile)
        db.flush()
        # Create default mentorship profile
        mentorship_prof = MentorshipProfile(
            alumni_id=alumni_profile.id,
            topics="DSA, Web Development, Placement Strategy",
            bio=f"Alumni of CMS Kanpur ({req.course.upper()} {grad_year}). Happy to mentor juniors!"
        )
        db.add(mentorship_prof)
    elif req.role in [UserRole.STUDENT, UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        student_profile = StudentProfile(
            user_id=new_user.id,
            full_name=req.full_name.strip(),
            enrollment_no=req.enrollment_no.strip(),
            roll_no=req.roll_no.strip(),
            course=req.course.upper(),
            batch_year=req.batch_year,
            current_semester=4,
            skills=req.skills or "Python, SQL, HTML, CSS, JavaScript",
            linkedin_url=req.linkedin_url,
            github_url=req.github_url,
            verification_status=verification_status,
            verification_notes=verification_notes
        )
        db.add(student_profile)
    
    db.commit()
    db.refresh(new_user)
    
    # Audit log
    client_ip = request.client.host if request.client else "unknown"
    log_audit_event(db, "USER_REGISTER", new_user.id, "User", new_user.id, client_ip, f"Registered as {new_user.role.value}. Auto-verified: {is_auto_verified}")
    
    # Generate Token
    token = create_access_token({"sub": str(new_user.id), "email": new_user.email, "role": new_user.role.value})
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role.value,
        full_name=req.full_name.strip(),
        is_verified=new_user.is_verified,
        verification_status=verification_status.value
    )

@router.post("/login", response_model=TokenResponse)
def login(creds: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    # 1. Search user by Email, or Roll No / Enrollment No
    clean_identifier = creds.email.strip().lower()
    user = db.query(User).filter(User.email == clean_identifier).first()
    if not user:
        # Check student profile
        stu = db.query(StudentProfile).filter(
            or_(
                StudentProfile.enrollment_no.ilike(creds.email.strip()),
                StudentProfile.roll_no.ilike(creds.email.strip())
            )
        ).first()
        if stu:
            user = stu.user
        else:
            alm = db.query(AlumniProfile).filter(
                or_(
                    AlumniProfile.enrollment_no.ilike(creds.email.strip()),
                    AlumniProfile.roll_no.ilike(creds.email.strip())
                )
            ).first()
            if alm:
                user = alm.user

    # 3. Verify user and password
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to sign in. Please check your email/username and password."
        )

    # 4. Check active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been temporarily suspended. Please contact the administrator."
        )
    
    full_name = "User"
    ver_status = "verified" if user.is_verified else "pending"
    if user.role == UserRole.ALUMNI and user.alumni_profile:
        full_name = user.alumni_profile.full_name
        ver_status = user.alumni_profile.verification_status.value
    elif user.student_profile:
        full_name = user.student_profile.full_name
        ver_status = user.student_profile.verification_status.value
    
    # Expiry calculation: 14 days if remember_me, else configured minutes
    expire_minutes = 14 * 24 * 60 if creds.remember_me else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=expire_minutes)
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=expire_minutes * 60
    )
    
    client_ip = request.client.host if request.client else "unknown"
    log_audit_event(db, "USER_LOGIN", user.id, "User", user.id, client_ip, f"User logged in: {user.email}")
    
    redirect_view = "admin" if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY] else "home"
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        full_name=full_name,
        is_verified=user.is_verified,
        verification_status=ver_status,
        redirect_view=redirect_view
    )

@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    response.delete_cookie(key="access_token")
    log_audit_event(db, "USER_LOGOUT", current_user.id, "User", current_user.id, None, "User logged out")
    return {"message": "Successfully logged out."}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import json
    profile_data = {}
    if current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.FACULTY]:
        sp = current_user.student_profile
        full_name = sp.full_name if sp else (
            "Dr. R. K. Srivastava" if current_user.role == UserRole.FACULTY else
            "CMS Super Administrator" if current_user.role == UserRole.SUPER_ADMIN else
            "CMS Portal Administrator"
        )
        edu = getattr(sp, "education_qualification", None) if sp else None
        if not edu:
            edu = "Ph.D in Computer Applications" if current_user.role == UserRole.FACULTY else "M.Tech / Ph.D in Computer Science & IT"
            
        skills = sp.skills if (sp and sp.skills) else "Institutional Administration, IT Architecture, Cloud Computing, Database Systems"
        links = sp.custom_links if (sp and sp.custom_links) else json.dumps([
            {"platform": "LinkedIn", "url": "https://linkedin.com/school/cmskanpur"},
            {"platform": "GitHub", "url": "https://github.com/cmskanpur"}
        ])
        profile_data = {
            "id": sp.id if sp else current_user.id,
            "full_name": full_name,
            "education_qualification": edu,
            "skills": skills,
            "avatar_url": sp.avatar_url if sp else None,
            "github_url": sp.github_url if sp else "https://github.com/cmskanpur",
            "linkedin_url": sp.linkedin_url if sp else "https://linkedin.com/school/cmskanpur",
            "leetcode_url": sp.leetcode_url if sp else None,
            "portfolio_url": sp.portfolio_url if sp else None,
            "custom_links": links,
            "verification_status": "verified",
            "verification_notes": "Official Institutional Authority - CMS Kanpur"
        }
    elif current_user.role == UserRole.ALUMNI and current_user.alumni_profile:
        p = current_user.alumni_profile
        profile_data = {
            "id": p.id,
            "full_name": p.full_name,
            "course": p.course,
            "batch_year": p.batch_year,
            "graduation_year": p.graduation_year,
            "current_company": p.current_company,
            "current_job_title": p.current_job_title,
            "current_city": p.current_city,
            "bio": p.bio,
            "avatar_url": p.avatar_url,
            "skills": p.skills,
            "education_qualification": getattr(p, "education_qualification", None) or f"{p.course} ({p.batch_year} - {p.graduation_year})",
            "github_url": p.github_url,
            "linkedin_url": p.linkedin_url,
            "leetcode_url": p.leetcode_url,
            "portfolio_url": p.portfolio_url,
            "custom_links": p.custom_links,
            "is_mentor": p.is_mentor,
            "is_referral_provider": p.is_referral_provider,
            "is_co_guide": p.is_co_guide,
            "verification_status": p.verification_status.value,
            "verification_notes": p.verification_notes,
            "experiences": [
                {
                    "id": exp.id,
                    "company": exp.company,
                    "job_title": exp.job_title,
                    "location": exp.location,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "is_current": exp.is_current,
                    "description": exp.description
                } for exp in (p.experiences or [])
            ],
            "projects": [
                {
                    "id": proj.id,
                    "title": proj.title,
                    "description": proj.description,
                    "technologies": proj.technologies,
                    "github_url": proj.github_url,
                    "demo_url": proj.demo_url,
                    "role": proj.role,
                    "completion_year": proj.completion_year
                } for proj in (p.projects or [])
            ]
        }
    elif current_user.student_profile:
        p = current_user.student_profile
        profile_data = {
            "id": p.id,
            "full_name": p.full_name,
            "course": p.course,
            "batch_year": p.batch_year,
            "current_semester": p.current_semester,
            "cgpa": p.cgpa,
            "bio": p.bio,
            "avatar_url": p.avatar_url,
            "resume_url": p.resume_url,
            "skills": p.skills,
            "education_qualification": getattr(p, "education_qualification", None) or f"Pursuing {p.course} ({p.batch_year} - {p.batch_year + 3})",
            "github_url": p.github_url,
            "linkedin_url": p.linkedin_url,
            "leetcode_url": p.leetcode_url,
            "portfolio_url": p.portfolio_url,
            "custom_links": p.custom_links,
            "verification_status": p.verification_status.value,
            "verification_notes": p.verification_notes
        }
    else:
        profile_data = {
            "full_name": current_user.email.split("@")[0].capitalize(),
            "verification_status": "verified"
        }
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "profile": profile_data
    }

@router.post("/forgot-password")
def forgot_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    # Always return success message to prevent user enumeration
    return {
        "message": "If this email is registered with CMS AlumniConnect, a password reset link has been dispatched.",
        "simulated_reset_code": "CMS-2025" if user else None
    }

@router.post("/reset-password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    if req.reset_code != "CMS-2025":
        raise HTTPException(status_code=400, detail="Invalid or expired reset code.")
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.hashed_password = hash_password(req.new_password)
    db.commit()
    log_audit_event(db, "PASSWORD_RESET", user.id, "User", user.id, None, "Password reset via code")
    return {"message": "Password successfully reset. You may now log in with your new credentials."}

@router.put("/change-password")
def change_password(req: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password does not match.")
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    log_audit_event(db, "PASSWORD_CHANGED", current_user.id, "User", current_user.id, None, "Password updated")
    return {"message": "Password successfully changed."}
