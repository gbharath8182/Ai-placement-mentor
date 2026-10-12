from html.parser import HTMLParser
from pathlib import Path

import pytest


FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
WORKSPACE_PAGES = ("dashboard", "roadmap", "analytics", "profile", "playground", "mock-interview", "resume", "aptitude", "cheatsheets", "topic")
AUTH_PAGES = ("login", "signup", "forgot-password", "reset-password")


class Page(HTMLParser):
    def __init__(self, name):
        super().__init__()
        self.elements = []
        self.feed((FRONTEND / f"{name}.html").read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attributes):
        self.elements.append((tag, dict(attributes)))


@pytest.mark.parametrize("name", WORKSPACE_PAGES + AUTH_PAGES + ("learn",))
def test_every_workspace_and_auth_page_loads_shared_shell(name):
    page = Page(name)
    assert sum(tag == "link" and attrs.get("href") == "/static/css/app.css" for tag, attrs in page.elements) == 1
    scripts = [attrs for tag, attrs in page.elements if tag == "script" and attrs.get("src") == "/static/js/app-shell.js"]
    assert len(scripts) == 1 and "defer" in scripts[0]


@pytest.mark.parametrize("name", WORKSPACE_PAGES)
def test_workspace_sources_keep_simple_navigation_without_legacy_icon_bar(name):
    page = Page(name)
    navigation = [attrs for tag, attrs in page.elements if tag == "nav" and attrs.get("aria-label") == "Primary"]
    assert len(navigation) == 1
    assert navigation[0].get("class") == "app-fallback-nav"
    assert navigation[0].get("aria-label") == "Primary"
    assert not any("dashboard-nav" in attrs.get("class", "").split() for tag, attrs in page.elements if tag == "nav")


def test_public_home_does_not_load_workspace_styles_or_shell():
    page = Page("index")
    assert not any(attrs.get("href") == "/static/css/app.css" or attrs.get("src") == "/static/js/app-shell.js" for tag, attrs in page.elements)


def test_dashboard_preserves_controls_and_has_no_decorative_svg():
    page = Page("dashboard")
    ids = [attrs["id"] for tag, attrs in page.elements if "id" in attrs]
    assert len(ids) == len(set(ids))
    assert {"hero-user-name", "stats-streak", "stats-completed", "domain-search", "domain-grid", "topics-drawer", "drawer-domain-title", "close-drawer-btn", "topic-list"} <= set(ids)
    assert not any(tag == "svg" for tag, attrs in page.elements)


def test_authenticated_catalog_loads_auth_before_shell():
    sources = [attrs["src"] for tag, attrs in Page("learn").elements if tag == "script" and "src" in attrs]
    assert sources.index("/static/js/auth.js") < sources.index("/static/js/app-shell.js")


def test_resume_has_pdf_controls_and_no_cdn_rendering_dependency():
    page = Page("resume")
    sources = [attrs["src"] for tag, attrs in page.elements if tag == "script" and "src" in attrs]
    assert all(source.startswith("/static/") for source in sources)
    text = (FRONTEND / "resume.html").read_text(encoding="utf-8")
    assert "Download PDF" in text and "Download .md" not in text
    assert any(attrs.get("id") == "resume-output" and "resume-paper" in attrs.get("class", "") for tag, attrs in page.elements)
