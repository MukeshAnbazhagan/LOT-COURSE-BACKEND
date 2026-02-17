from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.security import get_current_user
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/api/progress", tags=["lecture-progress"])

@router.post("/lectures/{lecture_id}", response_model=dict)
def update_lecture_progress(
    lecture_id: str,
    watched_duration: int,
    completed: bool,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update progress for a specific lecture"""
    user_id = current_user.get("user_id")
    
    # Get lecture and enrollment info
    lecture_info = db.execute(
        text("""
            SELECT cl.id, cl.course_id, cl.duration
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".course_lectures cl
            WHERE cl.id = :lecture_id
        """),
        {"lecture_id": lecture_id}
    ).fetchone()
    
    if not lecture_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    # Check if user is enrolled in the course
    enrollment = db.execute(
        text("""
            SELECT id FROM "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments
            WHERE user_id = :user_id AND course_id = :course_id
        """),
        {"user_id": user_id, "course_id": lecture_info.course_id}
    ).fetchone()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course"
        )
    
    # Check if progress record exists
    existing_progress = db.execute(
        text("""
            SELECT id FROM "94ba1d59-881d-444f-be73-b769590b6cc2".lecture_progress
            WHERE enrollment_id = :enrollment_id AND lecture_id = :lecture_id
        """),
        {"enrollment_id": enrollment.id, "lecture_id": lecture_id}
    ).fetchone()
    
    if existing_progress:
        # Update existing progress
        db.execute(
            text("""
                UPDATE "94ba1d59-881d-444f-be73-b769590b6cc2".lecture_progress
                SET watched_duration = :watched_duration,
                    completed = :completed,
                    completed_at = CASE WHEN :completed THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE id = :progress_id
            """),
            {
                "progress_id": existing_progress.id,
                "watched_duration": watched_duration,
                "completed": completed
            }
        )
        progress_id = existing_progress.id
    else:
        # Create new progress record
        progress_id = str(uuid4())
        db.execute(
            text("""
                INSERT INTO "94ba1d59-881d-444f-be73-b769590b6cc2".lecture_progress
                (id, enrollment_id, lecture_id, watched_duration, completed, completed_at)
                VALUES (:id, :enrollment_id, :lecture_id, :watched_duration, :completed, 
                        CASE WHEN :completed THEN CURRENT_TIMESTAMP ELSE NULL END)
            """),
            {
                "id": progress_id,
                "enrollment_id": enrollment.id,
                "lecture_id": lecture_id,
                "watched_duration": watched_duration,
                "completed": completed
            }
        )
    
    # Update overall course progress
    progress_stats = db.execute(
        text("""
            SELECT 
                COUNT(*) as total_lectures,
                COUNT(CASE WHEN lp.completed THEN 1 END) as completed_lectures
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".course_lectures cl
            LEFT JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".lecture_progress lp 
                ON cl.id = lp.lecture_id AND lp.enrollment_id = :enrollment_id
            WHERE cl.course_id = :course_id
        """),
        {"enrollment_id": enrollment.id, "course_id": lecture_info.course_id}
    ).fetchone()
    
    overall_progress = (progress_stats.completed_lectures / progress_stats.total_lectures * 100) if progress_stats.total_lectures > 0 else 0
    is_completed = progress_stats.completed_lectures == progress_stats.total_lectures
    
    db.execute(
        text("""
            UPDATE "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments
            SET progress = :progress,
                completed = :is_completed,
                completed_at = CASE WHEN :is_completed THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE id = :enrollment_id
        """),
        {
            "enrollment_id": enrollment.id,
            "progress": overall_progress,
            "is_completed": is_completed
        }
    )
    
    db.commit()
    
    return {
        "message": "Progress updated successfully",
        "lecture_progress_id": progress_id,
        "overall_progress": round(overall_progress, 2),
        "course_completed": is_completed
    }

@router.get("/courses/{course_id}", response_model=dict)
def get_course_lecture_progress(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed lecture-by-lecture progress for a course"""
    user_id = current_user.get("user_id")
    
    # Get enrollment
    enrollment = db.execute(
        text("""
            SELECT id FROM "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments
            WHERE user_id = :user_id AND course_id = :course_id
        """),
        {"user_id": user_id, "course_id": course_id}
    ).fetchone()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course"
        )
    
    # Get all lectures with progress
    lectures = db.execute(
        text("""
            SELECT 
                cl.id,
                cl.title,
                cl.duration,
                cl."order",
                COALESCE(lp.completed, FALSE) as completed,
                COALESCE(lp.watched_duration, 0) as watched_duration,
                lp.completed_at
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".course_lectures cl
            LEFT JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".lecture_progress lp 
                ON cl.id = lp.lecture_id AND lp.enrollment_id = :enrollment_id
            WHERE cl.course_id = :course_id
            ORDER BY cl."order" ASC
        """),
        {"enrollment_id": enrollment.id, "course_id": course_id}
    ).fetchall()
    
    lectures_data = []
    for lecture in lectures:
        lectures_data.append({
            "id": lecture.id,
            "title": lecture.title,
            "duration": lecture.duration,
            "order": lecture.order,
            "completed": lecture.completed,
            "watched_duration": lecture.watched_duration,
            "completed_at": lecture.completed_at.isoformat() if lecture.completed_at else None
        })
    
    return {
        "course_id": course_id,
        "lectures": lectures_data,
        "total_lectures": len(lectures_data),
        "completed_lectures": sum(1 for l in lectures_data if l["completed"])
    }