from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, Payment, Course, Event, Enrollment, EventRegistration
from app.schemas.payments import PaymentCreateRequest, PaymentVerifyRequest, PaymentInitResponse
from app.security import get_current_user
import razorpay
import os
import uuid

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Initialize Razorpay client (for RuPay in India)
razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID", ""),
        os.getenv("RAZORPAY_KEY_SECRET", "")
    )
)

@router.post("/create", response_model=dict)
def create_payment(
    payment_req: PaymentCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize payment for course enrollment or event registration"""
    
    # Validate course or event
    if payment_req.course_id:
        course = db.query(Course).filter(Course.id == payment_req.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        amount = course.price
    elif payment_req.event_id:
        event = db.query(Event).filter(Event.id == payment_req.event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        amount = payment_req.amount
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either course_id or event_id is required"
        )
    
    # Create Razorpay order
    try:
        order_data = {
            "amount": int(amount * 100),  # Amount in paise
            "currency": "INR",
            "receipt": str(uuid.uuid4()),
            "payment_capture": 1
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        # Store payment record with pending status
        payment = Payment(
            user_id=current_user.get("user_id"),
            course_id=payment_req.course_id,
            event_id=payment_req.event_id,
            amount=amount,
            payment_method=payment_req.payment_method,
            transaction_id=order['id'],
            status="pending"
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return {
            "order_id": order['id'],
            "amount": amount,
            "currency": "INR",
            "payment_method": payment_req.payment_method,
            "user_name": current_user.get("name", ""),
            "user_email": current_user.get("email", ""),
            "user_phone": current_user.get("phone", ""),
            "razorpay_key": os.getenv("RAZORPAY_KEY_ID", "")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initialization failed: {str(e)}"
        )

@router.post("/verify", response_model=dict)
def verify_payment(
    verify_req: PaymentVerifyRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify and complete payment"""
    
    # Find payment record
    payment = db.query(Payment).filter(
        Payment.transaction_id == verify_req.razorpay_order_id or
        Payment.transaction_id == verify_req.payment_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )
    
    try:
        # Verify signature with Razorpay
        if verify_req.razorpay_signature:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': verify_req.razorpay_order_id,
                'razorpay_payment_id': verify_req.razorpay_payment_id,
                'razorpay_signature': verify_req.razorpay_signature
            })
        
        # Update payment status
        payment.status = "completed"
        
        # Create enrollment or event registration
        if payment.course_id:
            # Check if already enrolled
            existing = db.query(Enrollment).filter(
                (Enrollment.user_id == current_user.get("user_id")) &
                (Enrollment.course_id == payment.course_id)
            ).first()
            
            if not existing:
                enrollment = Enrollment(
                    user_id=current_user.get("user_id"),
                    course_id=payment.course_id
                )
                db.add(enrollment)
                
                # Update course student count
                course = db.query(Course).filter(Course.id == payment.course_id).first()
                if course:
                    course.students_count += 1
        
        elif payment.event_id:
            # Check if already registered
            existing = db.query(EventRegistration).filter(
                (EventRegistration.user_id == current_user.get("user_id")) &
                (EventRegistration.event_id == payment.event_id)
            ).first()
            
            if not existing:
                registration = EventRegistration(
                    user_id=current_user.get("user_id"),
                    event_id=payment.event_id,
                    status="confirmed"
                )
                db.add(registration)
                
                # Update event registered count
                event = db.query(Event).filter(Event.id == payment.event_id).first()
                if event:
                    event.registered += 1
        
        db.commit()
        
        return {
            "message": "Payment verified successfully",
            "payment_id": payment.id,
            "status": "completed",
            "course_id": payment.course_id,
            "event_id": payment.event_id
        }
    
    except Exception as e:
        payment.status = "failed"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment verification failed: {str(e)}"
        )

@router.get("/transactions", response_model=dict)
def get_transactions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment transactions"""
    
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.get("user_id")
    ).all()
    
    transactions = []
    for payment in payments:
        trans_dict = {
            "id": payment.id,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "transaction_id": payment.transaction_id,
            "status": payment.status,
            "course_id": payment.course_id,
            "event_id": payment.event_id,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat()
        }
        transactions.append(trans_dict)
    
    return {
        "data": transactions,
        "total": len(transactions)
    }
