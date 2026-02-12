from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Course Schemas
class CourseBase(BaseModel):
    title: str
    description: str
    category: str
    level: str
    price: float
    duration: int
    image: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    image: Optional[str] = None

class CourseLectureBase(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    duration: int
    order: int

class CourseLectureResponse(CourseLectureBase):
    id: int
    course_id: int
    
    class Config:
        from_attributes = True

class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    instructor_name: str
    rating: float
    reviews_count: int
    students_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    curriculum: List[CourseLectureResponse] = []

class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    progress: float
    completed: bool
    enrolled_at: datetime
    
    class Config:
        from_attributes = True

# Event Schemas
class EventBase(BaseModel):
    title: str
    description: str
    event_type: str
    date: datetime
    time: str
    duration: int
    location: Optional[str] = None
    image: Optional[str] = None
    capacity: int
    event_url: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    duration: Optional[int] = None
    location: Optional[str] = None
    image: Optional[str] = None
    capacity: Optional[int] = None
    event_url: Optional[str] = None

class EventResponse(EventBase):
    id: int
    instructor_id: int
    instructor_name: str
    registered: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EventRegistrationResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    registered_at: datetime
    status: str
    
    class Config:
        from_attributes = True

class CourseReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class CourseReviewCreate(CourseReviewBase):
    pass

class CourseReviewResponse(CourseReviewBase):
    id: int
    course_id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
