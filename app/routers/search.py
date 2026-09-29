from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.user import AlumniProfile, StudentProfile, VerificationStatus
from app.models.job import Job
from app.models.project import IndustryProject
from app.models.resource import TechnicalResource
from app.models.event import Event

router = APIRouter(prefix="/api/search", tags=["Global Search Engine"])

@router.get("")
def global_search(
    q: str = Query(..., min_length=2, description="Universal search query"),
    db: Session = Depends(get_db)
):
    query_fmt = f"%{q.strip()}%"
    
    # 1. Search Alumni
    alumni_matches = db.query(AlumniProfile).filter(
        or_(
            AlumniProfile.full_name.ilike(query_fmt),
            AlumniProfile.current_company.ilike(query_fmt),
            AlumniProfile.current_job_title.ilike(query_fmt),
            AlumniProfile.skills.ilike(query_fmt)
        )
    ).limit(5).all()
    alumni_results = [
        {
            "id": a.id,
            "title": a.full_name,
            "subtitle": f"{a.current_job_title} at {a.current_company} ({a.course} '{a.batch_year})",
            "type": "alumni",
            "link": f"/alumni/{a.id}",
            "verified": a.verification_status == VerificationStatus.VERIFIED
        } for a in alumni_matches
    ]
    
    # 2. Search Jobs & Internships
    job_matches = db.query(Job).filter(
        Job.is_active == True,
        or_(
            Job.title.ilike(query_fmt),
            Job.company.ilike(query_fmt),
            Job.required_skills.ilike(query_fmt)
        )
    ).limit(5).all()
    job_results = [
        {
            "id": j.id,
            "title": j.title,
            "subtitle": f"{j.company} • {j.job_type.value.replace('_', ' ').title()} • {j.location}",
            "type": "job",
            "link": f"/jobs/{j.id}"
        } for j in job_matches
    ]
    
    # 3. Search Industry Projects
    project_matches = db.query(IndustryProject).filter(
        or_(
            IndustryProject.title.ilike(query_fmt),
            IndustryProject.domain.ilike(query_fmt),
            IndustryProject.required_technologies.ilike(query_fmt)
        )
    ).limit(5).all()
    project_results = [
        {
            "id": p.id,
            "title": p.title,
            "subtitle": f"Domain: {p.domain} • Tech: {p.required_technologies}",
            "type": "project",
            "link": f"/projects/{p.id}"
        } for p in project_matches
    ]
    
    # 4. Search Resources
    resource_matches = db.query(TechnicalResource).filter(
        TechnicalResource.is_approved == True,
        or_(
            TechnicalResource.title.ilike(query_fmt),
            TechnicalResource.tags.ilike(query_fmt)
        )
    ).limit(5).all()
    resource_results = [
        {
            "id": r.id,
            "title": r.title,
            "subtitle": f"Category: {r.category.name if r.category else 'Tech'} • {r.resource_type}",
            "type": "resource",
            "link": "/resources"
        } for r in resource_matches
    ]
    
    # 5. Search Events
    event_matches = db.query(Event).filter(
        Event.is_published == True,
        or_(
            Event.title.ilike(query_fmt),
            Event.description.ilike(query_fmt)
        )
    ).limit(5).all()
    event_results = [
        {
            "id": e.id,
            "title": e.title,
            "subtitle": f"{e.event_type.value.replace('_', ' ').title()} • {e.venue_or_link}",
            "type": "event",
            "link": f"/events/{e.id}"
        } for e in event_matches
    ]

    total_hits = len(alumni_results) + len(job_results) + len(project_results) + len(resource_results) + len(event_results)

    return {
        "query": q,
        "total_hits": total_hits,
        "results": {
            "alumni": alumni_results,
            "jobs": job_results,
            "projects": project_results,
            "resources": resource_results,
            "events": event_results
        }
    }
