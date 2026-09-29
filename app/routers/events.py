from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.event import Event, EventRegistration, EventType, EventRole
from app.schemas.event import EventCreate, EventRegisterRequest
from app.core.dependencies import get_current_user, get_optional_current_user, require_roles
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api/events", tags=["Events, Hackathons & Webinars"])

@router.get("")
def get_events(
    event_type: Optional[EventType] = Query(None),
    upcoming_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    query = db.query(Event).filter(Event.is_published == True)
    if event_type:
        query = query.filter(Event.event_type == event_type)
        
    events = query.order_by(Event.start_time.asc()).all()
    user_registrations = {}
    if current_user:
        regs = db.query(EventRegistration).filter(EventRegistration.user_id == current_user.id).all()
        user_registrations = {r.event_id: r.role_in_event.value for r in regs}
        
    results = []
    for e in events:
        organizer_name = "CMS Kanpur"
        if e.organizer and e.organizer.alumni_profile:
            organizer_name = e.organizer.alumni_profile.full_name
        elif e.organizer and e.organizer.student_profile:
            organizer_name = e.organizer.student_profile.full_name
            
        results.append({
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type.value,
            "description": e.description,
            "venue_or_link": e.venue_or_link,
            "is_online": e.is_online,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "capacity": e.capacity,
            "banner_image": e.banner_image,
            "speaker_info": e.speaker_info,
            "organizer_name": organizer_name,
            "registrations_count": len(e.registrations),
            "is_registered": e.id in user_registrations,
            "my_role": user_registrations.get(e.id)
        })
    return results

@router.get("/{event_id}")
def get_event_detail(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    e = db.query(Event).filter(Event.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found.")
        
    is_registered = False
    my_role = None
    if current_user:
        reg = db.query(EventRegistration).filter(EventRegistration.event_id == e.id, EventRegistration.user_id == current_user.id).first()
        if reg:
            is_registered = True
            my_role = reg.role_in_event.value

    return {
        "id": e.id,
        "title": e.title,
        "event_type": e.event_type.value,
        "description": e.description,
        "venue_or_link": e.venue_or_link,
        "is_online": e.is_online,
        "start_time": e.start_time.isoformat(),
        "end_time": e.end_time.isoformat(),
        "capacity": e.capacity,
        "banner_image": e.banner_image,
        "speaker_info": e.speaker_info,
        "registrations_count": len(e.registrations),
        "is_registered": is_registered,
        "my_role": my_role
    }

@router.post("")
def create_event(
    data: EventCreate,
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.ALUMNI])),
    db: Session = Depends(get_db)
):
    ev = Event(
        organizer_id=current_user.id,
        title=data.title,
        event_type=data.event_type,
        description=data.description,
        venue_or_link=data.venue_or_link,
        is_online=data.is_online,
        start_time=data.start_time,
        end_time=data.end_time,
        capacity=data.capacity,
        registration_deadline=data.registration_deadline,
        banner_image=data.banner_image,
        speaker_info=data.speaker_info,
        is_published=True
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    
    log_audit_event(db, "CREATE_EVENT", current_user.id, "Event", ev.id, None, f"Created event: {data.title}")
    return {"message": "Event published successfully!", "id": ev.id}

@router.post("/{event_id}/register")
def register_for_event(
    event_id: int,
    data: EventRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found.")
        
    existing = db.query(EventRegistration).filter(EventRegistration.event_id == ev.id, EventRegistration.user_id == current_user.id).first()
    if existing:
        existing.role_in_event = data.role_in_event
        db.commit()
        return {"message": f"Updated participation role to {data.role_in_event.value}."}
        
    reg = EventRegistration(
        event_id=ev.id,
        user_id=current_user.id,
        role_in_event=data.role_in_event
    )
    db.add(reg)
    db.commit()
    return {"message": f"Successfully registered as {data.role_in_event.value}!"}

@router.delete("/{event_id}/register")
def cancel_event_registration(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reg = db.query(EventRegistration).filter(EventRegistration.event_id == event_id, EventRegistration.user_id == current_user.id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found.")
    db.delete(reg)
    db.commit()
    return {"message": "Registration cancelled."}

@router.get("/{event_id}/participants")
def get_event_participants(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    regs = db.query(EventRegistration).filter(EventRegistration.event_id == event_id).all()
    results = []
    for r in regs:
        name = "Participant"
        role_label = r.user.role.value
        avatar = None
        if r.user.alumni_profile:
            name = r.user.alumni_profile.full_name
            avatar = r.user.alumni_profile.avatar_url
        elif r.user.student_profile:
            name = r.user.student_profile.full_name
            avatar = r.user.student_profile.avatar_url
            
        results.append({
            "user_id": r.user_id,
            "name": name,
            "user_role": role_label,
            "avatar_url": avatar,
            "participation_role": r.role_in_event.value,
            "registered_at": r.registered_at.isoformat()
        })
    return results
