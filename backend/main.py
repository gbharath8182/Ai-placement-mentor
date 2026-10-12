import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from pymongo.errors import PyMongoError
from backend.ai_provider import AIProviderError
from backend.middleware import SafetyMiddleware
from contextlib import asynccontextmanager

from backend.database import db_client
from backend.routes import auth, content, ai, practice, progress, domain_details, activity, analytics, mock_interview, resume, learning
from backend.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.JWT_SECRET or (settings.APP_ENV == "production" and len(settings.JWT_SECRET) < 32):
        raise RuntimeError("Configure JWT_SECRET with at least 32 random characters for production.")
    db_client.connect()
    try:
        await db_client.ping()
        yield
    finally:
        db_client.disconnect()

app = FastAPI(
    title="AI Placement Mentor API",
    description="Structured learning, evidence-based practice and contextual AI tutoring.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SafetyMiddleware)

# Mount API Routers
app.include_router(auth.router)
app.include_router(content.router)
app.include_router(ai.router)
app.include_router(practice.router)
app.include_router(progress.router)
app.include_router(domain_details.router)
app.include_router(activity.router)
app.include_router(analytics.router)
app.include_router(mock_interview.router)
app.include_router(resume.router)
app.include_router(learning.router)

@app.exception_handler(AIProviderError)
async def ai_provider_error(request: Request, error: AIProviderError):
    return JSONResponse(status_code=503 if error.kind != "rate_limit" else 429, content={"detail": error.message, "error": error.public()})

@app.exception_handler(PyMongoError)
async def database_error(request: Request, error: PyMongoError):
    return JSONResponse(status_code=503, content={"detail": "The learning database is temporarily unavailable. Please retry shortly.", "error": {"code": "database", "retryable": True}})

@app.get("/health/live")
async def liveness():
    return {"status": "ok", "service": "AI Placement Mentor"}

@app.get("/health/ready")
async def readiness():
    ready = await db_client.ping()
    return JSONResponse(status_code=200 if ready else 503, content={"status": "ready" if ready else "unavailable", "database": "connected" if ready else "unavailable"})

@app.get("/mock-interview")
async def mock_interview_page():
    return FileResponse("frontend/mock-interview.html")

# Ensure the frontend directory and subdirectories exist
os.makedirs("frontend/css", exist_ok=True)
os.makedirs("frontend/js", exist_ok=True)

# Mount static files folder
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Friendly HTML Routing
@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

@app.get("/learn")
async def read_public_curriculum():
    return FileResponse("frontend/learn.html")

@app.get("/login")
async def read_login():
    return FileResponse("frontend/login.html")

@app.get("/signup")
async def read_signup():
    return FileResponse("frontend/signup.html")

@app.get("/forgot-password")
async def read_forgot_password():
    return FileResponse("frontend/forgot-password.html")

@app.get("/reset-password")
async def read_reset_password():
    return FileResponse("frontend/reset-password.html")

@app.get("/dashboard")
async def read_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.get("/topic/{slug}")
async def read_topic_page(slug: str):
    # Returns topic.html; the client JS will fetch page content dynamically
    return FileResponse("frontend/topic.html")

@app.get("/aptitude")
async def read_aptitude_page():
    return FileResponse("frontend/aptitude.html")

@app.get("/playground")
async def read_playground_page():
    return FileResponse("frontend/playground.html")

@app.get("/cheatsheets")
async def read_cheatsheets_page():
    return FileResponse("frontend/cheatsheets.html")

@app.get("/roadmap")
async def read_roadmap_page():
    return FileResponse("frontend/roadmap.html")

@app.get("/profile")
async def read_profile_page():
    return FileResponse("frontend/profile.html")

@app.get("/analytics")
async def read_analytics_page():
    return FileResponse("frontend/analytics.html")

@app.get("/resume")
async def read_resume_page():
    return FileResponse("frontend/resume.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.PORT, reload=True)

