import re
from copy import deepcopy
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pymongo.errors import PyMongoError

from backend.middleware import SafetyMiddleware
from backend.routes import workspace
from backend.routes.content import builtin_curriculum, public_topic, serialize_doc
from tests.test_workspace import Collection, Cursor, OWNER, evidence, progress


class SearchableCollection(Collection):
    def find(self, query, projection):
        if "$and" not in query:
            return super().find(query, projection)
        documents = self.documents
        for condition in query["$and"]:
            documents = [document for document in documents if any(
                re.search(rule[field]["$regex"], str(document.get(field, "")), re.I)
                for rule in condition["$or"] for field in rule
            )]
        return Cursor(documents)


def create_app():
    app = FastAPI()
    app.add_middleware(SafetyMiddleware)
    curriculum = deepcopy(builtin_curriculum())
    first, second = curriculum["topics"][:2]
    collections = {
        "topics": SearchableCollection(curriculum["topics"]),
        "user_progress": Collection([progress(second["slug"])]),
        "user_mastery": Collection([evidence(first)]),
    }
    workspace.get_collection = collections.__getitem__
    app.include_router(workspace.router)
    app.dependency_overrides[workspace.get_current_user] = lambda: {"id": str(OWNER)}
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/curriculum")
    def catalog():
        return {"domains": curriculum["domains"], "topics": [{key: topic[key] for key in ("slug", "title", "domain_slug", "difficulty", "order", "objectives", "prerequisites")} for topic in curriculum["topics"]]}

    @app.get("/domains")
    @app.get("/domains/with-details")
    def domains():
        return [serialize_doc(domain) for domain in curriculum["domains"]]

    @app.get("/domains/{slug}/topics")
    def topics(slug):
        return [public_topic(topic) for topic in curriculum["topics"] if topic["domain_slug"] == slug]

    @app.get("/topics/{slug}")
    def topic(slug):
        match = next((topic for topic in curriculum["topics"] if topic["slug"] == slug), None)
        if not match:
            raise HTTPException(404)
        return public_topic(match)

    @app.get("/progress/{user_id}")
    def saved_progress(user_id):
        return [{"topic_slug": second["slug"], "status": "in_progress"}]

    @app.get("/activity/streak")
    def streak():
        return {"current_streak": 3, "longest_streak": 5}

    @app.exception_handler(PyMongoError)
    async def database_error(request, error):
        return JSONResponse({"detail": "Database unavailable"}, status_code=503)

    @app.get("/topic/{slug}")
    def lesson_page(slug):
        return FileResponse("frontend/topic.html")

    @app.get("/")
    def home():
        return FileResponse("frontend/index.html")

    @app.get("/{page}")
    def page(page):
        allowed = {path.stem for path in Path("frontend").glob("*.html")}
        if page not in allowed:
            raise HTTPException(404)
        return FileResponse(f"frontend/{page}.html")

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8883)
