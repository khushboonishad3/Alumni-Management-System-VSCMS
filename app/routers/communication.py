from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.models.user import User, UserRole
from app.models.communication import Conversation, Message, Notification
from app.models.audit import UserReport
from app.schemas.communication import MessageCreate
from app.core.dependencies import get_current_user
from app.core.audit import log_audit_event

router = APIRouter(prefix="/api", tags=["Messaging & Notifications"])

# ================= MESSAGING =================

@router.get("/conversations")
def get_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = db.query(Conversation).filter(
        or_(Conversation.participant1_id == current_user.id, Conversation.participant2_id == current_user.id)
    ).order_by(Conversation.updated_at.desc()).all()
    
    results = []
    for c in convs:
        other_user_id = c.participant2_id if c.participant1_id == current_user.id else c.participant1_id
        other_user = db.query(User).filter(User.id == other_user_id).first()
        if not other_user:
            continue
            
        other_name = other_user.email
        other_role = other_user.role.value
        other_avatar = None
        if other_user.alumni_profile:
            other_name = other_user.alumni_profile.full_name
            other_avatar = other_user.alumni_profile.avatar_url
        elif other_user.student_profile:
            other_name = other_user.student_profile.full_name
            other_avatar = other_user.student_profile.avatar_url
            
        last_msg = c.messages[-1] if c.messages else None
        unread = db.query(Message).filter(
            Message.conversation_id == c.id,
            Message.sender_id != current_user.id,
            Message.is_read == False
        ).count()
        
        results.append({
            "id": c.id,
            "other_user_id": other_user_id,
            "other_user_name": other_name,
            "other_user_role": other_role,
            "other_user_avatar": other_avatar,
            "last_message": last_msg.content if last_msg else None,
            "last_message_time": last_msg.created_at.isoformat() if last_msg else None,
            "unread_count": unread
        })
    return results

@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if conv.participant1_id != current_user.id and conv.participant2_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")
        
    # Mark messages as read
    db.query(Message).filter(
        Message.conversation_id == conv.id,
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    results = []
    for m in messages:
        sender_name = "User"
        if m.sender and m.sender.alumni_profile:
            sender_name = m.sender.alumni_profile.full_name
        elif m.sender and m.sender.student_profile:
            sender_name = m.sender.student_profile.full_name
            
        results.append({
            "id": m.id,
            "conversation_id": m.conversation_id,
            "sender_id": m.sender_id,
            "sender_name": sender_name,
            "is_me": m.sender_id == current_user.id,
            "content": m.content,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat()
        })
    return results

@router.post("/messages")
def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself.")
        
    recipient = db.query(User).filter(User.id == data.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found.")
        
    # Find or create conversation
    conv = db.query(Conversation).filter(
        or_(
            and_(Conversation.participant1_id == current_user.id, Conversation.participant2_id == recipient.id),
            and_(Conversation.participant1_id == recipient.id, Conversation.participant2_id == current_user.id)
        )
    ).first()
    
    if not conv:
        conv = Conversation(participant1_id=current_user.id, participant2_id=recipient.id)
        db.add(conv)
        db.flush()
        
    msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        content=data.content
    )
    db.add(msg)
    conv.updated_at = datetime.now(timezone.utc)
    
    # Notify recipient
    sender_name = current_user.student_profile.full_name if current_user.student_profile else (
        current_user.alumni_profile.full_name if current_user.alumni_profile else "A CMS Member"
    )
    notif = Notification(
        user_id=recipient.id,
        title=f"New Message from {sender_name}",
        message=f"{data.content[:60]}...",
        notification_type="message",
        link=f"/messages?conv={conv.id}"
    )
    db.add(notif)
    db.commit()
    
    return {"message": "Message sent.", "message_id": msg.id, "conversation_id": conv.id}

# ================= NOTIFICATIONS =================

@router.get("/notifications")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(30).all()
    unread_count = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).count()
    
    return {
        "unread_count": unread_count,
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "link": n.link,
                "notification_type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifs
        ]
    }

@router.put("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    n = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current_user.id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "Marked as read."}

@router.put("/notifications/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read."}

# ================= SAFETY & REPORTING =================

@router.post("/reports")
def create_report(
    reported_user_id: Optional[int] = Query(None),
    reason: str = Query(...),
    details: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rep = UserReport(
        reporter_id=current_user.id,
        reported_user_id=reported_user_id,
        reason=reason,
        details=details,
        status="pending"
    )
    db.add(rep)
    db.commit()
    log_audit_event(db, "REPORT_CONTENT", current_user.id, "UserReport", rep.id, None, f"Filed safety report: {reason}")
    return {"message": "Report submitted for administrator review."}
