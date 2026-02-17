from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.security import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("", response_model=dict)
def get_courses(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    instructor: Optional[str] = Query(None),  # NEW: Instructor filter
    priceMin: int = Query(0),
    priceMax: int = Query(10000),
    duration: Optional[str] = Query(None),
    limit: int = Query(12),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get all courses with filters (including instructor filter)"""
    
    query = """
        SELECT 
            c.*,
            u.name as instructor_name
        FROM "94ba1d59-881d-444f-be73-b769590b6cc2".courses c
        JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON c.instructor_id = u.id
        WHERE 1=1
    """
    params = {}
    
    # Apply filters
    if search:
        query += " AND (c.title ILIKE :search OR c.description ILIKE :search)"
        params["search"] = f"%{search}%"
    
    if category:
        query += " AND c.category = :category"
        params["category"] = category
    
    if level:
        query += " AND c.level = :level"
        params["level"] = level
    
    if instructor:
        query += " AND u.name ILIKE :instructor"
        params["instructor"] = f"%{instructor}%"
    
    query += " AND c.price BETWEEN :price_min AND :price_max"
    params["price_min"] = priceMin
    params["price_max"] = priceMax
    
    if duration:
        # Parse duration range like "1-4 weeks"
        if "-" in duration:
            parts = duration.split("-")
            if len(parts) == 2:
                try:
                    start = int(parts[0].strip().split()[0])
                    end = int(parts[1].strip().split()[0])
                    query += " AND c.duration BETWEEN :dur_start AND :dur_end"
                    params["dur_start"] = start
                    params["dur_end"] = end
                except:
                    pass
    
    # Get total count
    count_query = query.replace("SELECT c.*, u.name as instructor_name", "SELECT COUNT(*)")
    total = db.execute(text(count_query), params).scalar()
    
    # Get paginated results
    query += " ORDER BY c.created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    
    courses = db.execute(text(query), params).fetchall()
    
    courses_data = []
    for course in courses:
        courses_data.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "price": float(course.price),
            "duration": course.duration,
            "image": course.image,
            "rating": float(course.rating) if course.rating else 0,
            "reviews_count": course.reviews_count,
            "students_count": course.students_count,
            "instructor_id": course.instructor_id,
            "instructor_name": course.instructor_name,
            "created_at": course.created_at.isoformat(),
            "updated_at": course.updated_at.isoformat()
        })
    
    return {
        "data": courses_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{course_id}", response_model=dict)
def get_course(course_id: str, db: Session = Depends(get_db)):
    """Get course details with curriculum, instructor, and FAQs"""
    
    course = db.execute(
        text("""
            SELECT 
                c.*,
                u.name as instructor_name,
                u.bio as instructor_bio,
                u.profile_image as instructor_image
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".courses c
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON c.instructor_id = u.id
            WHERE c.id = :course_id
        """),
        {"course_id": course_id}
    ).fetchone()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get curriculum
    lectures = db.execute(
        text("""
            SELECT id, title, description, video_url, duration, "order"
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".course_lectures
            WHERE course_id = :course_id
            ORDER BY "order" ASC
        """),
        {"course_id": course_id}
    ).fetchall()
    
    curriculum = []
    for lecture in lectures:
        curriculum.append({
            "id": lecture.id,
            "title": lecture.title,
            "description": lecture.description,
            "video_url": lecture.video_url,
            "duration": lecture.duration,
            "order": lecture.order
        })
    
    # Get FAQs
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
    
    # Get reviews
    reviews = db.execute(
        text("""
            SELECT 
                cr.id,
                cr.rating,
                cr.comment,
                cr.created_at,
                u.name as user_name,
                u.profile_image as user_image
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".course_reviews cr
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON cr.user_id = u.id
            WHERE cr.course_id = :course_id
            ORDER BY cr.created_at DESC
            LIMIT 10
        """),
        {"course_id": course_id}
    ).fetchall()
    
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            "id": review.id,
            "rating": review.rating,
            "comment": review.comment,
            "user_name": review.user_name,
            "user_image": review.user_image,
            "created_at": review.created_at.isoformat()
        })
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "category": course.category,
        "level": course.level,
        "price": float(course.price),
        "duration": course.duration,
        "image": course.image,
        "rating": float(course.rating) if course.rating else 0,
        "reviews_count": course.reviews_count,
        "students_count": course.students_count,
        "instructor": {
            "id": course.instructor_id,
            "name": course.instructor_name,
            "bio": course.instructor_bio,
            "image": course.instructor_image
        },
        "curriculum": curriculum,
        "faqs": faqs_data,
        "reviews": reviews_data,
        "created_at": course.created_at.isoformat(),
        "updated_at": course.updated_at.isoformat()
    }

@router.get("/instructors/list", response_model=dict)
def get_instructors_list(db: Session = Depends(get_db)):
    """Get list of all instructors (for filter dropdown)"""
    
    instructors = db.execute(
        text("""
            SELECT DISTINCT 
                u.id,
                u.name,
                COUNT(c.id) as course_count
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".users u
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".courses c ON u.id = c.instructor_id
            WHERE u.role IN ('instructor', 'admin')
            GROUP BY u.id, u.name
            ORDER BY u.name ASC
        """)
    ).fetchall()
    
    instructors_data = []
    for instructor in instructors:
        instructors_data.append({
            "id": instructor.id,
            "name": instructor.name,
            "course_count": instructor.course_count
        })
    
    return {"data": instructors_data}