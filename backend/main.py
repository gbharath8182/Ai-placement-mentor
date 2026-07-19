import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from contextlib import asynccontextmanager

from backend.database import db_client
from backend.routes import auth, content, ai, practice, progress, domain_details, activity, analytics, mock_interview, resume
from backend.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    db_client.connect()
    yield
    # Shutdown actions
    db_client.disconnect()

app = FastAPI(
    title="AI-Assisted Learning Platform API",
    description="Backend for placement-focused adaptive learning platform with Groq and Pyodide compiler.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return FileResponse("frontend/login.html")

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

