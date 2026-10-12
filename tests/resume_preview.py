from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.ai_provider import Completion
from backend.routes import resume


WRITER_FIXTURE = """# Alex Morgan

## Summary
Backend developer with hands-on experience building Python APIs and accessible learning tools. Focused on clear interfaces, reliable data access and automated testing.

## Skills
- **Languages:** Python, JavaScript, SQL
- **Frameworks and tools:** FastAPI, MongoDB, Git, Docker, pytest

## Projects
### Study planner
- Built a scheduling API with authenticated access and user-scoped study records.
- Added automated tests for validation and account isolation.
- [Source](https://github.com/example/study-planner) / [Live demo](https://example.com/study%20planner)

### Resource library
- Created a searchable catalog of open educational resources with accessible navigation.

## Education
BSc Computer Science, Example University, 2026.

## Achievements & Certifications
- Presented the study planner at the university engineering showcase.
"""


def create_app():
    app = FastAPI()
    app.include_router(resume.router)
    app.dependency_overrides[resume.get_current_user] = lambda: {"id": "fixture-user"}
    resume.provider.complete = AsyncMock(return_value=Completion(WRITER_FIXTURE, "fixture-model"))
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/resume")
    def resume_page():
        return FileResponse(Path("frontend/resume.html"))

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8881)
