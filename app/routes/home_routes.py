from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter(prefix="/api/home", tags=["home"])

@router.get("/hero-slides", response_model=dict)
def get_hero_slides(db: Session = Depends(get_db)):
    """Get hero slider content (3 slides)"""
    
    slides = db.execute(
        text("""
            SELECT id, title, subtitle, description, image, cta_text, cta_link, countdown_date, "order"
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".hero_slides
            WHERE is_active = TRUE
            ORDER BY "order" ASC
            LIMIT 3
        """)
    ).fetchall()
    
    slides_data = []
    for slide in slides:
        slides_data.append({
            "id": slide.id,
            "title": slide.title,
            "subtitle": slide.subtitle,
            "description": slide.description,
            "image": slide.image,
            "cta_text": slide.cta_text,
            "cta_link": slide.cta_link,
            "countdown_date": slide.countdown_date.isoformat() if slide.countdown_date else None,
            "order": slide.order
        })
    
    return {"data": slides_data}

@router.get("/stats", response_model=dict)
def get_platform_stats(db: Session = Depends(get_db)):
    """Get platform statistics (50+ Courses | 10K Learners | 95% Completion | 4.8★)"""
    
    stats = db.execute(
        text("""
            SELECT id, stat_name, stat_value, stat_label, icon
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".platform_stats
            ORDER BY id ASC
        """)
    ).fetchall()
    
    stats_data = []
    for stat in stats:
        stats_data.append({
            "id": stat.id,
            "name": stat.stat_name,
            "value": stat.stat_value,
            "label": stat.stat_label,
            "icon": stat.icon
        })
    
    return {"data": stats_data}

@router.get("/featured-courses", response_model=dict)
def get_featured_courses(db: Session = Depends(get_db)):
    """Get featured courses (4-card carousel)"""
    
    courses = db.execute(
        text("""
            SELECT 
                c.id, c.title, c.description, c.price, c.image, 
                c.rating, c.reviews_count, c.level, c.duration,
                u.name as instructor_name
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".courses c
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON c.instructor_id = u.id
            ORDER BY c.rating DESC, c.students_count DESC
            LIMIT 4
        """)
    ).fetchall()
    
    courses_data = []
    for course in courses:
        courses_data.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "price": course.price,
            "image": course.image,
            "rating": course.rating,
            "reviews_count": course.reviews_count,
            "level": course.level,
            "duration": course.duration,
            "instructor_name": course.instructor_name
        })
    
    return {"data": courses_data}

@router.get("/upcoming-events", response_model=dict)
def get_upcoming_events(db: Session = Depends(get_db)):
    """Get upcoming events (3-card carousel)"""
    
    events = db.execute(
        text("""
            SELECT 
                e.id, e.title, e.description, e.date, e.time, 
                e.image, e.event_type, e.capacity, e.registered,
                u.name as instructor_name
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".events e
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON e.instructor_id = u.id
            WHERE e.date >= CURRENT_DATE
            ORDER BY e.date ASC
            LIMIT 3
        """)
    ).fetchall()
    
    events_data = []
    for event in events:
        events_data.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date.strftime("%Y-%m-%d"),
            "time": event.time,
            "image": event.image,
            "event_type": event.event_type,
            "capacity": event.capacity,
            "registered": event.registered,
            "instructor_name": event.instructor_name
        })
    
    return {"data": events_data}

@router.get("/testimonials", response_model=dict)
def get_testimonials(db: Session = Depends(get_db)):
    """Get testimonials (3 cards)"""
    
    testimonials = db.execute(
        text("""
            SELECT id, name, role, avatar, rating, comment, created_at
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".testimonials
            WHERE is_featured = TRUE
            ORDER BY created_at DESC
            LIMIT 3
        """)
    ).fetchall()
    
    testimonials_data = []
    for test in testimonials:
        testimonials_data.append({
            "id": test.id,
            "name": test.name,
            "role": test.role,
            "avatar": test.avatar,
            "rating": test.rating,
            "comment": test.comment,
            "created_at": test.created_at.isoformat()
        })
    
    return {"data": testimonials_data}