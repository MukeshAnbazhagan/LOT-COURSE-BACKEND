from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from security import get_current_user
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("", response_model=dict)
def get_events(
    search: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(12),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get all events with filters"""
    
    query = """
        SELECT 
            e.*,
            u.name as instructor_name
        FROM "94ba1d59-881d-444f-be73-b769590b6cc2".events e
        JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON e.instructor_id = u.id
        WHERE 1=1
    """
    params = {}
    
    # Apply filters
    if search:
        query += " AND (e.title ILIKE :search OR e.description ILIKE :search)"
        params["search"] = f"%{search}%"
    
    if event_type:
        query += " AND e.event_type = :event_type"
        params["event_type"] = event_type
    
    if date_from:
        query += " AND e.date >= :date_from"
        params["date_from"] = date_from
    
    if date_to:
        query += " AND e.date <= :date_to"
        params["date_to"] = date_to
    
    query += " ORDER BY e.date ASC"
    
    # Get total count
    count_query = query.replace("SELECT e.*, u.name as instructor_name", "SELECT COUNT(*)")
    total = db.execute(text(count_query), params).scalar()
    
    # Get paginated results
    query += " LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    
    events = db.execute(text(query), params).fetchall()
    
    events_data = []
    for event in events:
        events_data.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "date": event.date.strftime("%Y-%m-%d"),
            "time": event.time,
            "duration": event.duration,
            "location": event.location,
            "image": event.image,
            "capacity": event.capacity,
            "registered": event.registered,
            "event_url": event.event_url,
            "instructor_id": event.instructor_id,
            "instructor_name": event.instructor_name,
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat()
        })
    
    return {
        "data": events_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{event_id}", response_model=dict)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Get event details with agenda, instructor, and registrants count"""
    
    event = db.execute(
        text("""
            SELECT 
                e.*,
                u.name as instructor_name,
                u.bio as instructor_bio,
                u.profile_image as instructor_image
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".events e
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON e.instructor_id = u.id
            WHERE e.id = :event_id
        """),
        {"event_id": event_id}
    ).fetchone()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get agenda
    agenda_items = db.execute(
        text("""
            SELECT id, title, description, start_time, end_time, speaker, "order"
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".event_agenda
            WHERE event_id = :event_id
            ORDER BY "order" ASC
        """),
        {"event_id": event_id}
    ).fetchall()
    
    agenda = []
    for item in agenda_items:
        agenda.append({
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "speaker": item.speaker,
            "order": item.order
        })
    
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "date": event.date.strftime("%Y-%m-%d"),
        "time": event.time,
        "duration": event.duration,
        "location": event.location,
        "image": event.image,
        "capacity": event.capacity,
        "registered": event.registered,
        "event_url": event.event_url,
        "instructor": {
            "id": event.instructor_id,
            "name": event.instructor_name,
            "bio": event.instructor_bio,
            "image": event.instructor_image
        },
        "agenda": agenda,
        "created_at": event.created_at.isoformat(),
        "updated_at": event.updated_at.isoformat()
    }

@router.post("/{event_id}/rsvp", response_model=dict)
def rsvp_event(
    event_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """RSVP for event with WhatsApp confirmation"""
    
    user_id = current_user.get("user_id")
    
    # Get event details
    event = db.execute(
        text("""
            SELECT 
                e.*,
                u.name as user_name,
                u.phone as user_phone
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".events e,
                 "94ba1d59-881d-444f-be73-b769590b6cc2".users u
            WHERE e.id = :event_id AND u.id = :user_id
        """),
        {"event_id": event_id, "user_id": user_id}
    ).fetchone()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check capacity
    if event.registered >= event.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is full"
        )
    
    # Check if already registered
    existing = db.execute(
        text("""
            SELECT id FROM "94ba1d59-881d-444f-be73-b769590b6cc2".event_registrations
            WHERE user_id = :user_id AND event_id = :event_id
        """),
        {"user_id": user_id, "event_id": event_id}
    ).fetchone()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this event"
        )
    
    # Create registration
    from uuid import uuid4
    registration_id = str(uuid4())
    
    db.execute(
        text("""
            INSERT INTO "94ba1d59-881d-444f-be73-b769590b6cc2".event_registrations
            (id, user_id, event_id, status)
            VALUES (:id, :user_id, :event_id, 'confirmed')
        """),
        {"id": registration_id, "user_id": user_id, "event_id": event_id}
    )
    
    # Update registered count
    db.execute(
        text("""
            UPDATE "94ba1d59-881d-444f-be73-b769590b6cc2".events
            SET registered = registered + 1
            WHERE id = :event_id
        """),
        {"event_id": event_id}
    )
    
    db.commit()
    
    # Send WhatsApp confirmation
    try:
        from app.services.whatsapp_service import whatsapp_service
        whatsapp_service.send_event_rsvp_message(
            to_phone=event.user_phone,
            user_name=event.user_name,
            event_title=event.title,
            event_date=event.date.strftime("%Y-%m-%d"),
            event_time=event.time,
            event_link=event.event_url
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send WhatsApp notification: {str(e)}")
    
    return {
        "message": "Successfully registered for event",
        "registration_id": registration_id,
        "event_url": event.event_url,
        "calendar_download": f"/api/events/{event_id}/calendar"
    }

@router.get("/{event_id}/calendar", response_model=dict)
def get_calendar_file(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Generate .ics calendar file for event"""
    
    event = db.execute(
        text("""
            SELECT title, description, date, time, duration, location, event_url
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".events
            WHERE id = :event_id
        """),
        {"event_id": event_id}
    ).fetchone()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Generate .ics file content
    # This is a simplified version - in production, use icalendar library
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//LOT Platform//Event//EN
BEGIN:VEVENT
SUMMARY:{event.title}
DESCRIPTION:{event.description}
DTSTART:{event.date.strftime('%Y%m%d')}T{event.time.replace(':', '')}00
DURATION:PT{event.duration}M
LOCATION:{event.location or 'Online'}
URL:{event.event_url or ''}
END:VEVENT
END:VCALENDAR"""
    
    return {
        "filename": f"{event.title.replace(' ', '_')}.ics",
        "content": ics_content,
        "content_type": "text/calendar"
    }

@router.get("/my-schedule", response_model=dict)
def get_my_schedule(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's registered events"""
    
    user_id = current_user.get("user_id")
    
    registrations = db.execute(
        text("""
            SELECT 
                e.id,
                e.title,
                e.date,
                e.time,
                e.duration,
                e.event_type,
                e.event_url,
                e.location,
                u.name as instructor_name,
                er.status,
                er.registered_at
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".event_registrations er
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".events e ON er.event_id = e.id
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON e.instructor_id = u.id
            WHERE er.user_id = :user_id
            ORDER BY e.date ASC
        """),
        {"user_id": user_id}
    ).fetchall()
    
    events_data = []
    for reg in registrations:
        events_data.append({
            "id": reg.id,
            "title": reg.title,
            "date": reg.date.strftime("%Y-%m-%d"),
            "time": reg.time,
            "duration": reg.duration,
            "event_type": reg.event_type,
            "location": reg.location,
            "instructor_name": reg.instructor_name,
            "event_url": reg.event_url,
            "registration_status": reg.status,
            "registered_at": reg.registered_at.isoformat()
        })
    
    return {
        "data": events_data,
        "total": len(events_data)
    }