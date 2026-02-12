from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaymentCreateRequest(BaseModel):
    course_id: Optional[int] = None
    event_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    payment_method: str = "rupay"  # Default to RuPay for India

class PaymentVerifyRequest(BaseModel):
    payment_id: str
    razorpay_signature: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    user_id: int
    course_id: Optional[int] = None
    event_id: Optional[int] = None
    amount: float
    payment_method: str
    transaction_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaymentInitResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    payment_method: str
    user_name: str
    user_email: str
    user_phone: str
