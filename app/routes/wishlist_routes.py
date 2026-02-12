from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from security import get_current_user
from uuid import uuid4

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])

@router.post("/add/{course_id}", response_model=dict)
def add_to_wishlist(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add course to wishlist"""
    user_id = current_user.get("user_id")
    
    # Check if course exists
    course_check = db.execute(
        text("SELECT id FROM \"94ba1d59-881d-444f-be73-b769590b6cc2\".courses WHERE id = :course_id"),
        {"course_id": course_id}
    ).fetchone()
    
    if not course_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if already in wishlist
    existing = db.execute(
        text("""
            SELECT id FROM "94ba1d59-881d-444f-be73-b769590b6cc2".wishlist 
            WHERE user_id = :user_id AND course_id = :course_id
        """),
        {"user_id": user_id, "course_id": course_id}
    ).fetchone()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course already in wishlist"
        )
    
    # Add to wishlist
    wishlist_id = str(uuid4())
    db.execute(
        text("""
            INSERT INTO "94ba1d59-881d-444f-be73-b769590b6cc2".wishlist 
            (id, user_id, course_id) 
            VALUES (:id, :user_id, :course_id)
        """),
        {"id": wishlist_id, "user_id": user_id, "course_id": course_id}
    )
    db.commit()
    
    return {"message": "Course added to wishlist", "wishlist_id": wishlist_id}

@router.delete("/remove/{course_id}", response_model=dict)
def remove_from_wishlist(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove course from wishlist"""
    user_id = current_user.get("user_id")
    
    result = db.execute(
        text("""
            DELETE FROM "94ba1d59-881d-444f-be73-b769590b6cc2".wishlist 
            WHERE user_id = :user_id AND course_id = :course_id
            RETURNING id
        """),
        {"user_id": user_id, "course_id": course_id}
    )
    db.commit()
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found in wishlist"
        )
    
    return {"message": "Course removed from wishlist"}

@router.get("", response_model=dict)
def get_wishlist(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's wishlist"""
    user_id = current_user.get("user_id")
    
    wishlist_items = db.execute(
        text("""
            SELECT 
                w.id,
                w.course_id,
                w.created_at,
                c.title,
                c.description,
                c.price,
                c.image,
                c.rating,
                c.level,
                u.name as instructor_name
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".wishlist w
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".courses c ON w.course_id = c.id
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON c.instructor_id = u.id
            WHERE w.user_id = :user_id
            ORDER BY w.created_at DESC
        """),
        {"user_id": user_id}
    ).fetchall()
    
    items_data = []
    for item in wishlist_items:
        items_data.append({
            "id": item.id,
            "course_id": item.course_id,
            "title": item.title,
            "description": item.description,
            "price": item.price,
            "image": item.image,
            "rating": item.rating,
            "level": item.level,
            "instructor_name": item.instructor_name,
            "added_at": item.created_at.isoformat()
        })
    
    return {
        "data": items_data,
        "total": len(items_data)
    }