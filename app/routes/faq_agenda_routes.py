from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.security import get_current_user
from uuid import uuid4
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["faq-agenda"])

# ==================== COURSE FAQ SCHEMAS ====================

class CourseFAQCreate(BaseModel):
    question: str
    answer: str
    order: Optional[int] = 0

class CourseFAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    order: Optional[int] = None

# ==================== EVENT AGENDA SCHEMAS ====================

class EventAgendaCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    speaker: Optional[str] = None
    order: Optional[int] = 0

class EventAgendaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    speaker: Optional[str] = None
    order: Optional[int] = None

# ==================== COURSE FAQ ENDPOINTS ====================

@router.get("/courses/{course_id}/faqs", response_model=dict)
def get_course_faqs(
    course_id: str,
    db: Session = Depends(get_db)
):
    """Get all FAQs for a course"""
    
    faqs = db.execute(
        text("""
            SELECT id, question, answer, "order"
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".course_faqs
            WHERE course_id = :course_id
            ORDER BY "order" ASC
        """),
        {"course_id": course_id}
    ).fetchall()
    
    faqs_data = []
    for faq in faqs:
        faqs_data.append({
            "id": faq.id,
            "question": faq.question,
            "answer": faq.answer,
            "order": faq.order
        })
    
    return {"data": faqs_data}

@router.post("/courses/{course_id}/faqs", response_model=dict)
def create_course_faq(
    course_id: str,
    faq_data: CourseFAQCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create FAQ for a course (instructor/admin only)"""
    
    # Check if course exists and user is instructor or admin
    course = db.execute(
        text("""
            SELECT instructor_id FROM "94ba1d59-881d-444f-be73-b769590b6cc2".courses
            WHERE id = :course_id
        """),
        {"course_id": course_id}
    ).fetchone()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    user_role = current_user.get("role")
    if user_role not in ["admin", "instructor"] and course.instructor_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course instructor or admin can add FAQs"
        )
    
    faq_id = str(uuid4())
    db.execute(
        text("""
            INSERT INTO "94ba1d59-881d-444f-be73-b769590b6cc2".course_faqs
            (id, course_id, question, answer, "order")
            VALUES (:id, :course_id, :question, :answer, :order)
        """),
        {
            "id": faq_id,
            "course_id": course_id,
            "question": faq_data.question,
            "answer": faq_data.answer,
            "order": faq_data.order
        }
    )
    db.commit()
    
    return {"message": "FAQ created successfully", "faq_id": faq_id}

@router.put("/faqs/{faq_id}", response_model=dict)
def update_course_faq(
    faq_id: str,
    faq_data: CourseFAQUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a course FAQ"""
    
    # Build update query dynamically
    updates = []
    params = {"faq_id": faq_id}
    
    if faq_data.question is not None:
        updates.append('question = :question')
        params["question"] = faq_data.question
    
    if faq_data.answer is not None:
        updates.append('answer = :answer')
        params["answer"] = faq_data.answer
    
    if faq_data.order is not None:
        updates.append('"order" = :order')
        params["order"] = faq_data.order
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    query = f"""
        UPDATE "94ba1d59-881d-444f-be73-b769590b6cc2".course_faqs
        SET {', '.join(updates)}
        WHERE id = :faq_id
        RETURNING id
    """
    
    result = db.execute(text(query), params)
    db.commit()
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    return {"message": "FAQ updated successfully"}

@router.delete("/faqs/{faq_id}", response_model=dict)
def delete_course_faq(
    faq_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a course FAQ"""
    
    result = db.execute(
        text("""
            DELETE FROM "94ba1d59-881d-444f-be73-b769590b6cc2".course_faqs
            WHERE id = :faq_id
            RETURNING id
        """),
        {"faq_id": faq_id}
    )
    db.commit()
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    return {"message": "FAQ deleted successfully"}

# ==================== EVENT AGENDA ENDPOINTS ====================

@router.get("/events/{event_id}/agenda", response_model=dict)
def get_event_agenda(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get agenda for an event"""
    
    agenda_items = db.execute(
        text("""
            SELECT id, title, description, start_time, end_time, speaker, "order"
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".event_agenda
            WHERE event_id = :event_id
            ORDER BY "order" ASC
        """),
        {"event_id": event_id}
    ).fetchall()
    
    agenda_data = []
    for item in agenda_items:
        agenda_data.append({
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "speaker": item.speaker,
            "order": item.order
        })
    
    return {"data": agenda_data}

@router.post("/events/{event_id}/agenda", response_model=dict)
def create_event_agenda(
    event_id: str,
    agenda_data: EventAgendaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create agenda item for event (instructor/admin only)"""
    
    # Check if event exists and user is instructor or admin
    event = db.execute(
        text("""
            SELECT instructor_id FROM "94ba1d59-881d-444f-be73-b769590b6cc2".events
            WHERE id = :event_id
        """),
        {"event_id": event_id}
    ).fetchone()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    user_role = current_user.get("role")
    if user_role not in ["admin", "instructor"] and event.instructor_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event instructor or admin can add agenda"
        )
    
    agenda_id = str(uuid4())
    db.execute(
        text("""
            INSERT INTO "94ba1d59-881d-444f-be73-b769590b6cc2".event_agenda
            (id, event_id, title, description, start_time, end_time, speaker, "order")
            VALUES (:id, :event_id, :title, :description, :start_time, :end_time, :speaker, :order)
        """),
        {
            "id": agenda_id,
            "event_id": event_id,
            "title": agenda_data.title,
            "description": agenda_data.description,
            "start_time": agenda_data.start_time,
            "end_time": agenda_data.end_time,
            "speaker": agenda_data.speaker,
            "order": agenda_data.order
        }
    )
    db.commit()
    
    return {"message": "Agenda item created successfully", "agenda_id": agenda_id}

@router.get("/events/{event_id}/registrants", response_model=dict)
def get_event_registrants(
    event_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users registered for an event"""
    
    registrants = db.execute(
        text("""
            SELECT 
                u.id,
                u.name,
                u.email,
                er.status,
                er.registered_at
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".event_registrations er
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON er.user_id = u.id
            WHERE er.event_id = :event_id
            ORDER BY er.registered_at DESC
        """),
        {"event_id": event_id}
    ).fetchall()
    
    registrants_data = []
    for reg in registrants:
        registrants_data.append({
            "id": reg.id,
            "name": reg.name,
            "email": reg.email,
            "status": reg.status,
            "registered_at": reg.registered_at.isoformat()
        })
    
    return {
        "data": registrants_data,
        "total": len(registrants_data)
    }