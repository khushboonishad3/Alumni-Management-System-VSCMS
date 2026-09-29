from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.project import (
    IndustryProject, ProjectProposal, ProjectMilestone,
    ProjectDifficulty, ProjectStatus, ProposalStatus
)
from app.models.communication import Notification
from app.schemas.project import ProjectCreate, ProjectProposalCreate, MilestoneCreate
from app.core.dependencies import get_current_user, get_optional_current_user, require_roles
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api/projects", tags=["Industry Projects & Co-Guidance"])

@router.get("")
def get_projects(
    domain: Optional[str] = Query(None),
    difficulty: Optional[ProjectDifficulty] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(IndustryProject)
    if domain:
        query = query.filter(IndustryProject.domain.ilike(f"%{domain.strip()}%"))
    if difficulty:
        query = query.filter(IndustryProject.difficulty == difficulty)
    if q:
        query = query.filter(IndustryProject.title.ilike(f"%{q.strip()}%"))
        
    projects = query.order_by(IndustryProject.created_at.desc()).all()
    results = []
    for p in projects:
        creator_name = "CMS Member"
        company = "CMS Kanpur"
        if p.creator and p.creator.alumni_profile:
            creator_name = p.creator.alumni_profile.full_name
            company = p.creator.alumni_profile.current_company or "CMS Alumnus"
        elif p.creator and p.creator.student_profile:
            creator_name = p.creator.student_profile.full_name
            company = "CMS Faculty" if p.creator.role == UserRole.FACULTY else "CMS Administration"
        elif p.creator:
            creator_name = p.creator.email.split("@")[0].capitalize()
            company = "CMS Administration" if p.creator.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN] else ("CMS Faculty" if p.creator.role == UserRole.FACULTY else "CMS Kanpur")
            
        results.append({
            "id": p.id,
            "creator_id": p.creator_id,
            "creator_name": creator_name,
            "creator_company": company,
            "title": p.title,
            "description": p.description,
            "domain": p.domain,
            "required_technologies": [t.strip() for t in p.required_technologies.split(",") if t.strip()],
            "required_technologies_raw": p.required_technologies,
            "difficulty": p.difficulty.value,
            "expected_outcome": p.expected_outcome,
            "duration_weeks": p.duration_weeks,
            "max_students": p.max_students,
            "status": p.status.value,
            "created_at": p.created_at.isoformat(),
            "proposals_count": len(p.proposals),
            "milestones_count": len(p.milestones)
        })
    return results

@router.get("/{project_id}")
def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db)
):
    p = db.query(IndustryProject).filter(IndustryProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project problem statement not found.")
        
    creator_name = "CMS Member"
    company = "CMS Kanpur"
    if p.creator and p.creator.alumni_profile:
        creator_name = p.creator.alumni_profile.full_name
        company = p.creator.alumni_profile.current_company or "CMS Alumnus"
    elif p.creator and p.creator.student_profile:
        creator_name = p.creator.student_profile.full_name
        company = "CMS Faculty" if p.creator.role == UserRole.FACULTY else "CMS Administration"
    elif p.creator:
        creator_name = p.creator.email.split("@")[0].capitalize()
        company = "CMS Administration" if p.creator.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN] else ("CMS Faculty" if p.creator.role == UserRole.FACULTY else "CMS Kanpur")
        
    return {
        "id": p.id,
        "creator_id": p.creator_id,
        "creator_name": creator_name,
        "creator_company": company,
        "title": p.title,
        "description": p.description,
        "domain": p.domain,
        "required_technologies": [t.strip() for t in p.required_technologies.split(",") if t.strip()],
        "required_technologies_raw": p.required_technologies,
        "difficulty": p.difficulty.value,
        "expected_outcome": p.expected_outcome,
        "duration_weeks": p.duration_weeks,
        "max_students": p.max_students,
        "status": p.status.value,
        "created_at": p.created_at.isoformat(),
        "milestones": [
            {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "due_date": m.due_date,
                "is_completed": m.is_completed,
                "submission_url": m.submission_url
            } for m in p.milestones
        ]
    }

@router.post("")
def create_project_problem(
    data: ProjectCreate,
    current_user: User = Depends(require_roles([UserRole.ALUMNI, UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    project = IndustryProject(
        creator_id=current_user.id,
        title=data.title,
        description=data.description,
        domain=data.domain,
        required_technologies=data.required_technologies,
        difficulty=data.difficulty,
        expected_outcome=data.expected_outcome,
        duration_weeks=data.duration_weeks,
        max_students=data.max_students,
        status=ProjectStatus.APPROVED
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    log_audit_event(db, "CREATE_PROJECT_PROBLEM", current_user.id, "IndustryProject", project.id, None, f"Created problem statement: {data.title}")
    return {"message": "Industry project problem statement posted successfully!", "id": project.id}

@router.post("/{project_id}/proposals")
def submit_proposal(
    project_id: int,
    data: ProjectProposalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(IndustryProject).filter(IndustryProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    prop = ProjectProposal(
        project_id=p.id,
        student_team_lead_id=current_user.id,
        team_members=data.team_members,
        proposal_text=data.proposal_text,
        proposal_document_url=data.proposal_document_url,
        status=ProposalStatus.SUBMITTED
    )
    db.add(prop)
    
    # Notify creator
    student_name = current_user.student_profile.full_name if current_user.student_profile else "A student team"
    notif = Notification(
        user_id=p.creator_id,
        title="New Project Proposal Submitted",
        message=f"{student_name} submitted a solution proposal for '{p.title}'.",
        notification_type="general",
        link=f"/projects/{p.id}"
    )
    db.add(notif)
    db.commit()
    
    return {"message": "Proposal submitted successfully!", "proposal_id": prop.id}

@router.get("/{project_id}/proposals")
def get_project_proposals(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(IndustryProject).filter(IndustryProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if p.creator_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY]:
        raise HTTPException(status_code=403, detail="Forbidden.")
        
    proposals = db.query(ProjectProposal).filter(ProjectProposal.project_id == project_id).all()
    results = []
    for prop in proposals:
        lead_name = prop.team_lead.student_profile.full_name if (prop.team_lead and prop.team_lead.student_profile) else "Team Lead"
        results.append({
            "id": prop.id,
            "team_lead_id": prop.student_team_lead_id,
            "team_lead_name": lead_name,
            "team_members": prop.team_members,
            "proposal_text": prop.proposal_text,
            "proposal_document_url": prop.proposal_document_url,
            "status": prop.status.value,
            "feedback": prop.feedback,
            "submitted_at": prop.submitted_at.isoformat()
        })
    return results

@router.put("/proposals/{proposal_id}/status")
def update_proposal_status(
    proposal_id: int,
    status_val: ProposalStatus = Query(...),
    feedback: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prop = db.query(ProjectProposal).filter(ProjectProposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if prop.project.creator_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY]:
        raise HTTPException(status_code=403, detail="Forbidden.")
        
    prop.status = status_val
    if feedback:
        prop.feedback = feedback
        
    # Notify team lead
    notif = Notification(
        user_id=prop.student_team_lead_id,
        title="Project Proposal Update",
        message=f"Your proposal for '{prop.project.title}' is now: {status_val.value.title()}.",
        notification_type="general",
        link=f"/projects/{prop.project_id}"
    )
    db.add(notif)
    db.commit()
    return {"message": "Proposal status updated."}

@router.post("/{project_id}/milestones")
def add_milestone(
    project_id: int,
    data: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(IndustryProject).filter(IndustryProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if p.creator_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY]:
        raise HTTPException(status_code=403, detail="Forbidden.")
        
    m = ProjectMilestone(
        project_id=p.id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        is_completed=False
    )
    db.add(m)
    db.commit()
    return {"message": "Milestone created.", "id": m.id}
