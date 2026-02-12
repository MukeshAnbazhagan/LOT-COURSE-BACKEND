from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Wishlist Schemas
class WishlistCreate(BaseModel):
    course_id: str

class WishlistResponse(BaseModel):
    id: str
    user_id: str
    course_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Badge Schemas
class BadgeResponse(BaseModel):
    id: str
    badge_name: str
    badge_description: Optional[str]
    badge_icon: Optional[str]
    earned_at: datetime
    
    class Config:
        from_attributes = True

# Course FAQ Schemas
class CourseFAQCreate(BaseModel):
    question: str
    answer: str
    order: Optional[int] = 0

class CourseFAQResponse(BaseModel):
    id: str
    course_id: str
    question: str
    answer: str
    order: int
    
    class Config:
        from_attributes = True

# Event Agenda Schemas
class EventAgendaCreate(BaseModel):
    title: str
    description: Optional[str]
    start_time: str
    end_time: str
    speaker: Optional[str]
    order: Optional[int] = 0

class EventAgendaResponse(BaseModel):
    id: str
    event_id: str
    title: str
    description: Optional[str]
    start_time: str
    end_time: str
    speaker: Optional[str]
    order: int
    
    class Config:
        from_attributes = True

# WhatsApp Message Schemas
class WhatsAppMessageCreate(BaseModel):
    phone_number: str
    message_type: str
    message_content: str
    course_id: Optional[str] = None
    event_id: Optional[str] = None

class WhatsAppMessageResponse(BaseModel):
    id: str
    user_id: str
    phone_number: str
    message_type: str
    status: str
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Platform Stats Schemas
class PlatformStatsResponse(BaseModel):
    id: str
    stat_name: str
    stat_value: str
    stat_label: Optional[str]
    icon: Optional[str]
    
    class Config:
        from_attributes = True

# Testimonial Schemas
class TestimonialCreate(BaseModel):
    name: str
    role: Optional[str]
    avatar: Optional[str]
    rating: int
    comment: str
    course_id: Optional[str] = None

class TestimonialResponse(BaseModel):
    id: str
    name: str
    role: Optional[str]
    avatar: Optional[str]
    rating: int
    comment: str
    course_id: Optional[str]
    is_featured: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Hero Slide Schemas
class HeroSlideCreate(BaseModel):
    title: str
    subtitle: Optional[str]
    description: Optional[str]
    image: Optional[str]
    cta_text: Optional[str]
    cta_link: Optional[str]
    countdown_date: Optional[datetime]
    order: Optional[int] = 0

class HeroSlideResponse(BaseModel):
    id: str
    title: str
    subtitle: Optional[str]
    description: Optional[str]
    image: Optional[str]
    cta_text: Optional[str]
    cta_link: Optional[str]
    countdown_date: Optional[datetime]
    order: int
    is_active: bool
    
    class Config:
        from_attributes = True

# Lecture Progress Schemas
class LectureProgressUpdate(BaseModel):
    lecture_id: str
    watched_duration: int
    completed: bool

class LectureProgressResponse(BaseModel):
    id: str
    lecture_id: str
    completed: bool
    watched_duration: int
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Admin Analytics Schemas
class AnalyticsMetric(BaseModel):
    metric_name: str
    metric_value: float
    metric_date: datetime
    additional_data: Optional[dict] = None