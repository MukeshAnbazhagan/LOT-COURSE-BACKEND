from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, Enrollment, EventRegistration, Certificate, User
from app.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/overview", response_model=dict)
def get_overview(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard overview with stats"""
    
    user_id = current_user.get("user_id")
    
    # Get enrollments
    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()
    
    # Get event registrations
    registrations = db.query(EventRegistration).filter(
        EventRegistration.user_id == user_id
    ).all()
    
    # Get certificates
    certificates = db.query(Certificate).filter(
        Certificate.user_id == user_id
    ).all()
    
    # Calculate stats
    completed_courses = sum(1 for e in enrollments if e.completed)
    avg_progress = sum(e.progress for e in enrollments) / len(enrollments) if enrollments else 0
    
    return {
        "total_courses": len(enrollments),
        "completed_courses": completed_courses,
        "in_progress_courses": len(enrollments) - completed_courses,
        "upcoming_events": len(registrations),
        "certificates_earned": len(certificates),
        "average_progress": round(avg_progress, 2),
        "badges": ["Fast Learner", "Consistent"] if completed_courses >= 2 else []
    }

@router.get("/my-courses", response_model=dict)
def get_my_courses(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's enrolled courses"""
    
    user_id = current_user.get("user_id")
    
    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()
    
    courses_data = []
    for enrollment in enrollments:
        course = enrollment.course
        course_dict = {
            "id": course.id,
            "title": course.title,
            "instructor_name": course.instructor.name,
            "progress": enrollment.progress,
            "completed": enrollment.completed,
            "image": course.image,
            "level": course.level,
            "enrolled_at": enrollment.enrolled_at.isoformat()
        }
        courses_data.append(course_dict)
    
    return {
        "data": courses_data,
        "total": len(courses_data)
    }

@router.get("/progress", response_model=dict)
def get_progress(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed course progress"""
    
    user_id = current_user.get("user_id")
    
    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()
    
    progress_data = []
    for enrollment in enrollments:
        course = enrollment.course
        
        # Calculate progress
        total_lectures = len(course.curriculum)
        completed_lectures = len([lp for lp in enrollment.progress_details if lp.completed])
        
        progress_dict = {
            "course_id": course.id,
            "course_title": course.title,
            "total_lectures": total_lectures,
            "completed_lectures": completed_lectures,
            "progress_percentage": (completed_lectures / total_lectures * 100) if total_lectures > 0 else 0,
            "completed": enrollment.completed,
            "last_accessed": enrollment.updated_at.isoformat() if enrollment.updated_at else None
        }
        progress_data.append(progress_dict)
    
    return {
        "data": progress_data,
        "total": len(progress_data)
    }

@router.get("/certificates", response_model=dict)
def get_certificates(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's certificates"""
    
    user_id = current_user.get("user_id")
    
    certificates = db.query(Certificate).filter(
        Certificate.user_id == user_id
    ).all()
    
    certs_data = []
    for cert in certificates:
        cert_dict = {
            "id": cert.id,
            "course_title": cert.course.title if cert.course else "Unknown Course",
            "certificate_number": cert.certificate_number,
            "issued_at": cert.issued_at.isoformat(),
            "certificate_url": cert.certificate_url
        }
        certs_data.append(cert_dict)
    
    return {
        "data": certs_data,
        "total": len(certs_data)
    }
