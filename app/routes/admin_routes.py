from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.security import get_current_user
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])

def check_admin(current_user: dict = Depends(get_current_user)):
    """Verify user is admin"""
    if current_user.get("role") != "admin" and current_user.get("role") != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# ==================== DASHBOARD ANALYTICS ====================

@router.get("/analytics/overview", response_model=dict)
def get_admin_overview(
    admin: dict = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard overview statistics"""
    
    # Total counts
    total_users = db.execute(
        text('SELECT COUNT(*) FROM "94ba1d59-881d-444f-be73-b769590b6cc2".users')
    ).scalar()
    
    total_courses = db.execute(
        text('SELECT COUNT(*) FROM "94ba1d59-881d-444f-be73-b769590b6cc2".courses')
    ).scalar()
    
    total_enrollments = db.execute(
        text('SELECT COUNT(*) FROM "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments')
    ).scalar()
    
    total_events = db.execute(
        text('SELECT COUNT(*) FROM "94ba1d59-881d-444f-be73-b769590b6cc2".events')
    ).scalar()
    
    # Revenue
    total_revenue = db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".payments 
            WHERE status = 'completed'
        """)
    ).scalar()
    
    # Recent activity (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
    
    new_users_30d = db.execute(
        text("""
            SELECT COUNT(*) FROM "94ba1d59-881d-444f-be73-b769590b6cc2".users 
            WHERE created_at >= :date
        """),
        {"date": thirty_days_ago}
    ).scalar()
    
    new_enrollments_30d = db.execute(
        text("""
            SELECT COUNT(*) FROM "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments 
            WHERE enrolled_at >= :date
        """),
        {"date": thirty_days_ago}
    ).scalar()
    
    revenue_30d = db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".payments 
            WHERE status = 'completed' AND created_at >= :date
        """),
        {"date": thirty_days_ago}
    ).scalar()
    
    return {
        "total_users": total_users,
        "total_courses": total_courses,
        "total_enrollments": total_enrollments,
        "total_events": total_events,
        "total_revenue": float(total_revenue),
        "last_30_days": {
            "new_users": new_users_30d,
            "new_enrollments": new_enrollments_30d,
            "revenue": float(revenue_30d)
        }
    }

@router.get("/analytics/revenue", response_model=dict)
def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Get revenue analytics for specified number of days"""
    
    start_date = (datetime.now() - timedelta(days=days)).date()
    
    daily_revenue = db.execute(
        text("""
            SELECT 
                DATE(created_at) as date,
                SUM(amount) as revenue,
                COUNT(*) as transactions
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".payments
            WHERE status = 'completed' AND created_at >= :start_date
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """),
        {"start_date": start_date}
    ).fetchall()
    
    data = []
    for row in daily_revenue:
        data.append({
            "date": row.date.isoformat(),
            "revenue": float(row.revenue),
            "transactions": row.transactions
        })
    
    total_revenue = sum(d["revenue"] for d in data)
    
    return {
        "period_days": days,
        "total_revenue": total_revenue,
        "daily_data": data
    }

@router.get("/analytics/enrollments", response_model=dict)
def get_enrollment_analytics(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Get enrollment analytics"""
    
    start_date = (datetime.now() - timedelta(days=days)).date()
    
    daily_enrollments = db.execute(
        text("""
            SELECT 
                DATE(enrolled_at) as date,
                COUNT(*) as enrollments
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments
            WHERE enrolled_at >= :start_date
            GROUP BY DATE(enrolled_at)
            ORDER BY date ASC
        """),
        {"start_date": start_date}
    ).fetchall()
    
    data = []
    for row in daily_enrollments:
        data.append({
            "date": row.date.isoformat(),
            "enrollments": row.enrollments
        })
    
    return {
        "period_days": days,
        "total_enrollments": sum(d["enrollments"] for d in data),
        "daily_data": data
    }

@router.get("/analytics/popular-courses", response_model=dict)
def get_popular_courses(
    limit: int = Query(10, ge=1, le=50),
    admin: dict = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Get most popular courses by enrollment"""
    
    courses = db.execute(
        text("""
            SELECT 
                c.id,
                c.title,
                c.students_count,
                c.rating,
                c.price,
                COUNT(e.id) as total_enrollments,
                SUM(CASE WHEN e.completed THEN 1 ELSE 0 END) as completions
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".courses c
            LEFT JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments e ON c.id = e.course_id
            GROUP BY c.id
            ORDER BY total_enrollments DESC
            LIMIT :limit
        """),
        {"limit": limit}
    ).fetchall()
    
    data = []
    for course in courses:
        data.append({
            "id": course.id,
            "title": course.title,
            "students_count": course.students_count,
            "rating": float(course.rating) if course.rating else 0,
            "price": float(course.price),
            "total_enrollments": course.total_enrollments or 0,
            "completions": course.completions or 0,
            "completion_rate": (course.completions / course.total_enrollments * 100) if course.total_enrollments > 0 else 0
        })
    
    return {"data": data}

# ==================== USER MANAGEMENT ====================

@router.get("/users", response_model=dict)
def get_all_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    admin: dict = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Get all users with filters"""
    
    query = 'SELECT * FROM "94ba1d59-881d-444f-be73-b769590b6cc2".users WHERE 1=1'
    params = {}
    
    if search:
        query += " AND (name ILIKE :search OR email ILIKE :search)"
        params["search"] = f"%{search}%"
    
    if role:
        query += " AND role = :role"
        params["role"] = role
    
    # Get total count
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    total = db.execute(text(count_query), params).scalar()
    
    # Get paginated results
    query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    
    users = db.execute(text(query), params).fetchall()
    
    users_data = []
    for user in users:
        users_data.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        })
    
    return {
        "data": users_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.put("/users/{user_id}/role", response_model=dict)
def update_user_role(
    user_id: str,
    new_role: str,
    admin: dict = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Update user role (student, instructor, admin)"""
    
    if new_role not in ["student", "instructor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be student, instructor, or admin"
        )
    
    result = db.execute(
        text("""
            UPDATE "94ba1d59-881d-444f-be73-b769590b6cc2".users
            SET role = :role
            WHERE id = :user_id
            RETURNING id
        """),
        {"user_id": user_id, "role": new_role}
    )
    db.commit()
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": f"User role updated to {new_role}"}

# ==================== PAYMENT MANAGEMENT ====================

@router.get("/payments", response_model=dict)
def get_all_payments(
    status_filter: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    admin: dict = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Get all payment transactions"""
    
    query = """
        SELECT 
            p.*,
            u.name as user_name,
            u.email as user_email,
            c.title as course_title,
            e.title as event_title
        FROM "94ba1d59-881d-444f-be73-b769590b6cc2".payments p
        JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON p.user_id = u.id
        LEFT JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".courses c ON p.course_id = c.id
        LEFT JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".events e ON p.event_id = e.id
        WHERE 1=1
    """
    params = {}
    
    if status_filter:
        query += " AND p.status = :status"
        params["status"] = status_filter
    
    # Get total
    count_query = query.replace("SELECT p.*,", "SELECT COUNT(*),").replace(
        "u.name as user_name, u.email as user_email, c.title as course_title, e.title as event_title", ""
    )
    total = db.execute(text(count_query), params).scalar()
    
    # Get paginated
    query += " ORDER BY p.created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    
    payments = db.execute(text(query), params).fetchall()
    
    payments_data = []
    for p in payments:
        payments_data.append({
            "id": p.id,
            "user_name": p.user_name,
            "user_email": p.user_email,
            "course_title": p.course_title,
            "event_title": p.event_title,
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "transaction_id": p.transaction_id,
            "status": p.status,
            "created_at": p.created_at.isoformat()
        })
    
    return {
        "data": payments_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }