path = "backend/main.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

if "resume" in content and "from backend.routes import" in content and "resume" in content.split("from backend.routes import")[1].split("\n")[0]:
    print("SKIPPED: main.py import already patched")
else:
    old_import = "from backend.routes import auth, content, ai, practice, progress, domain_details, activity, analytics, mock_interview"
    assert old_import in content, "PATCH FAILED: import line not found - check current main.py content"
    new_import = old_import + ", resume"
    content = content.replace(old_import, new_import)

    old_router = "app.include_router(mock_interview.router)"
    assert content.count(old_router) == 1, "PATCH FAILED: mock_interview router line not found or not unique"
    new_router = old_router + "\r\napp.include_router(resume.router)"
    content = content.replace(old_router, new_router)

    old_route_anchor = '@app.get("/analytics")\r\nasync def read_analytics_page():\r\n    return FileResponse("frontend/analytics.html")'
    assert old_route_anchor in content, "PATCH FAILED: analytics page route not found - check current main.py content"
    new_route = old_route_anchor + '\r\n\r\n@app.get("/resume")\r\nasync def read_resume_page():\r\n    return FileResponse("frontend/resume.html")'
    content = content.replace(old_route_anchor, new_route)

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print("main.py patched successfully")