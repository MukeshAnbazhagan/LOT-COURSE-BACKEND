from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from .env file - Uses PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/lot_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False           # Set to True for SQL logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class UserRole(str, enum.Enum):
    admin = "admin"
    instructor = "instructor"
    student = "student"

class EventType(str, enum.Enum):
    workshop = "workshop"
    live_event = "live_event"
    online_quiz = "online_quiz"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.student)
    profile_image = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    courses = relationship("Course", back_populates="instructor")
    events = relationship("Event", back_populates="instructor")
    enrollments = relationship("Enrollment", back_populates="user")
    event_registrations = relationship("EventRegistration", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String, index=True)
    level = Column(String)  # Beginner, Intermediate, Advanced
    price = Column(Float)
    duration = Column(Integer)  # in weeks
    instructor_id = Column(Integer, ForeignKey("users.id"))
    image = Column(String, nullable=True)
    rating = Column(Float, default=0)
    reviews_count = Column(Integer, default=0)
    students_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    instructor = relationship("User", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")
    curriculum = relationship("CourseLecture", back_populates="course")
    reviews = relationship("CourseReview", back_populates="course")

class CourseLecture(Base):
    __tablename__ = "course_lectures"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    duration = Column(Integer)  # in minutes
    order = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    course = relationship("Course", back_populates="curriculum")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    progress = Column(Float, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    progress_details = relationship("LectureProgress", back_populates="enrollment")

class LectureProgress(Base):
    __tablename__ = "lecture_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"))
    lecture_id = Column(Integer, ForeignKey("course_lectures.id"))
    completed = Column(Boolean, default=False)
    watched_duration = Column(Integer, default=0)  # in seconds
    completed_at = Column(DateTime, nullable=True)
    
    enrollment = relationship("Enrollment", back_populates="progress_details")

class CourseReview(Base):
    __tablename__ = "course_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    course = relationship("Course", back_populates="reviews")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    event_type = Column(SQLEnum(EventType))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, index=True)
    time = Column(String)
    duration = Column(Integer)  # in minutes
    location = Column(String, nullable=True)
    image = Column(String, nullable=True)
    capacity = Column(Integer)
    registered = Column(Integer, default=0)
    event_url = Column(String, nullable=True)  # For online events
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    instructor = relationship("User", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event")

class EventRegistration(Base):
    __tablename__ = "event_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    registered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="confirmed")  # confirmed, cancelled
    
    # Relationships
    user = relationship("User", back_populates="event_registrations")
    event = relationship("Event", back_populates="registrations")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    amount = Column(Float)
    payment_method = Column(String)  # rupay, stripe, etc.
    transaction_id = Column(String, unique=True, index=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.pending)
    payment_gateway_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")

class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    certificate_url = Column(String)
    issued_at = Column(DateTime, default=datetime.utcnow)
    certificate_number = Column(String, unique=True)

# def init_db():
#     # Drop all tables first (only for development)
    
#     # Create all tables in correct order
#     # Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()