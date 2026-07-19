path = "backend/main.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

old_import = "from backend.routes import auth, content, ai, practice, progress, domain_details, activity, analytics"
new_import = "from backend.routes import auth, content, ai, practice, progress, domain_details, activity, analytics, mock_interview"
assert old_import in content, "PATCH FAILED: import line not found - main.py changed since it was last read"
content = content.replace(old_import, new_import)

old_router = "app.include_router(analytics.router)"
assert content.count(old_router) == 1, "PATCH FAILED: router line not found or not unique"
new_router = "app.include_router(analytics.router)\r\napp.include_router(mock_interview.router)"
content = content.replace(old_router, new_router)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("main.py patched successfully")