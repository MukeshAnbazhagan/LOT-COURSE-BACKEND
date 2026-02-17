from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from app.routes import auth, dashboard, payments
from app.routes.courses import router as courses_router
from app.routes.events import router as events_router
from app.routes.wishlist_routes import router as wishlist_router
from app.routes.home_routes import router as home_router
from app.routes.lecture_progress_routes import router as lecture_progress_router
from app.routes.admin_routes import router as admin_router
from app.routes.faq_agenda_routes import router as faq_agenda_router
from app.routes.certificate_routes import router as certificates_router


# Initialize FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "LOT Platform API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Learning Online Together - Professional LMS Platform",
)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Health & Root Endpoints
# -------------------------

@app.get("/", tags=["root"])
async def root():
    return {
        "message": "LOT Platform API",
        "version": app.version,
        "status": "running",
    }

@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "app": app.title,
        "version": app.version,
    }

@app.get("/api", tags=["api"])
async def api_root():
    return {
        "message": "Welcome to LOT Platform API",
        "version": app.version,
        "endpoints": {
            "auth": "/api/auth",
            "courses": "/api/courses",
            "events": "/api/events",
            "payments": "/api/payments",
            "dashboard": "/api/dashboard",
            "wishlist": "/api/wishlist",
            "home": "/api/home",
            "progress": "/api/progress",
            "admin": "/api/admin",
            "certificates": "/api/certificates",
        },
    }

# -------------------------
# Include Routers
# -------------------------
# NOTE: Routers already have their prefixes defined, don't add them again!

app.include_router(auth.router)                  # Already has prefix="/api/auth"
app.include_router(courses_router)                # Already has prefix="/api/courses"
app.include_router(events_router)                 # Already has prefix="/api/events"
app.include_router(payments.router)               # Already has prefix="/api/payments"
app.include_router(dashboard.router)              # Already has prefix="/api/dashboard"
app.include_router(wishlist_router)               # Already has prefix="/api/wishlist"
app.include_router(home_router)                   # Already has prefix="/api/home"
app.include_router(lecture_progress_router)       # Already has prefix="/api/progress"
app.include_router(admin_router)                  # Already has prefix="/api/admin"
app.include_router(faq_agenda_router)             # Already has prefix="/api"
app.include_router(certificates_router)           # Already has prefix="/api/certificates"

# -------------------------
# Global Exception Handler
# -------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if os.getenv("DEBUG") == "True" else "An error occurred",
        },
    )

# -------------------------
# Local Dev Entry Point
# -------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False") == "True",
    )