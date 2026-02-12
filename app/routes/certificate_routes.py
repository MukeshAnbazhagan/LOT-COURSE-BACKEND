from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from security import get_current_user
from uuid import uuid4
from datetime import datetime
import random
import string

router = APIRouter(prefix="/api/certificates", tags=["certificates"])

def generate_certificate_number(course_id: str, user_id: str) -> str:
    """Generate unique certificate number"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CERT-{timestamp}-{random_suffix}"

@router.post("/generate/{course_id}", response_model=dict)
def generate_certificate(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate certificate for completed course"""
    
    user_id = current_user.get("user_id")
    
    # Check if enrollment exists and course is completed
    enrollment = db.execute(
        text("""
            SELECT id, completed 
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".enrollments
            WHERE user_id = :user_id AND course_id = :course_id
        """),
        {"user_id": user_id, "course_id": course_id}
    ).fetchone()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    if not enrollment.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must be completed to generate certificate"
        )
    
    # Check if certificate already exists
    existing_cert = db.execute(
        text("""
            SELECT id, certificate_url, certificate_number 
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".certificates
            WHERE user_id = :user_id AND course_id = :course_id
        """),
        {"user_id": user_id, "course_id": course_id}
    ).fetchone()
    
    if existing_cert:
        return {
            "message": "Certificate already exists",
            "certificate_id": existing_cert.id,
            "certificate_url": existing_cert.certificate_url,
            "certificate_number": existing_cert.certificate_number
        }
    
    # Get course and user details
    course_user = db.execute(
        text("""
            SELECT 
                c.title as course_title,
                u.name as user_name,
                u.phone as user_phone
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".courses c,
                 "94ba1d59-881d-444f-be73-b769590b6cc2".users u
            WHERE c.id = :course_id AND u.id = :user_id
        """),
        {"course_id": course_id, "user_id": user_id}
    ).fetchone()
    
    # Generate certificate
    cert_id = str(uuid4())
    cert_number = generate_certificate_number(course_id, user_id)
    
    # In production, this would generate actual PDF certificate
    # For now, we'll use a placeholder URL
    cert_url = f"https://certificates.lotplatform.com/{cert_number}.pdf"
    
    db.execute(
        text("""
            INSERT INTO "94ba1d59-881d-444f-be73-b769590b6cc2".certificates
            (id, user_id, course_id, certificate_url, certificate_number)
            VALUES (:id, :user_id, :course_id, :cert_url, :cert_number)
        """),
        {
            "id": cert_id,
            "user_id": user_id,
            "course_id": course_id,
            "cert_url": cert_url,
            "cert_number": cert_number
        }
    )
    db.commit()
    
    # Send WhatsApp notification
    try:
        from app.services.whatsapp_service import whatsapp_service
        whatsapp_service.send_certificate_message(
            to_phone=course_user.user_phone,
            user_name=course_user.user_name,
            course_title=course_user.course_title,
            certificate_url=cert_url
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send WhatsApp notification: {str(e)}")
    
    # Award badge if first certificate
    total_certs = db.execute(
        text("""
            SELECT COUNT(*) FROM "94ba1d59-881d-444f-be73-b769590b6cc2".certificates
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).scalar()
    
    if total_certs == 1:
        # Award "First Course Complete" badge
        badge_id = str(uuid4())
        db.execute(
            text("""
                INSERT INTO "94ba1d59-881d-444f-be73-b769590b6cc2".user_badges
                (id, user_id, badge_name, badge_description, badge_icon)
                VALUES (:id, :user_id, :name, :desc, :icon)
            """),
            {
                "id": badge_id,
                "user_id": user_id,
                "name": "First Course Complete",
                "desc": "Completed your first course",
                "icon": "trophy"
            }
        )
        db.commit()
    
    return {
        "message": "Certificate generated successfully",
        "certificate_id": cert_id,
        "certificate_url": cert_url,
        "certificate_number": cert_number
    }

@router.get("/my-certificates", response_model=dict)
def get_my_certificates(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certificates for current user"""
    
    user_id = current_user.get("user_id")
    
    certificates = db.execute(
        text("""
            SELECT 
                cert.id,
                cert.certificate_number,
                cert.certificate_url,
                cert.issued_at,
                c.title as course_title,
                c.image as course_image
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".certificates cert
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".courses c ON cert.course_id = c.id
            WHERE cert.user_id = :user_id
            ORDER BY cert.issued_at DESC
        """),
        {"user_id": user_id}
    ).fetchall()
    
    certs_data = []
    for cert in certificates:
        certs_data.append({
            "id": cert.id,
            "certificate_number": cert.certificate_number,
            "certificate_url": cert.certificate_url,
            "issued_at": cert.issued_at.isoformat(),
            "course_title": cert.course_title,
            "course_image": cert.course_image
        })
    
    return {
        "data": certs_data,
        "total": len(certs_data)
    }

@router.get("/verify/{certificate_number}", response_model=dict)
def verify_certificate(
    certificate_number: str,
    db: Session = Depends(get_db)
):
    """Publicly verify a certificate by certificate number"""
    
    certificate = db.execute(
        text("""
            SELECT 
                cert.id,
                cert.certificate_number,
                cert.issued_at,
                u.name as user_name,
                c.title as course_title
            FROM "94ba1d59-881d-444f-be73-b769590b6cc2".certificates cert
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".users u ON cert.user_id = u.id
            JOIN "94ba1d59-881d-444f-be73-b769590b6cc2".courses c ON cert.course_id = c.id
            WHERE cert.certificate_number = :cert_number
        """),
        {"cert_number": certificate_number}
    ).fetchone()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return {
        "valid": True,
        "certificate_number": certificate.certificate_number,
        "user_name": certificate.user_name,
        "course_title": certificate.course_title,
        "issued_at": certificate.issued_at.isoformat()
    }