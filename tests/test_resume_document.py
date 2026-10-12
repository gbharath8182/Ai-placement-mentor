from io import BytesIO

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pypdf import PdfReader

from backend.resume_document import ResumeDocument, ResumeSpan, build_resume_document, normalize_web_url, render_resume_pdf
from backend.routes import resume


FACTS = {
    "full_name": "Alex Morgan", "target_role": "Backend engineer", "email": "alex@example.com",
    "github_url": "https://github.com/example", "linkedin_url": "https://www.linkedin.com/in/example",
    "portfolio_url": "https://example.com/my portfolio?category=backend&language=Python",
    "projects": [{"title": "Study planner", "description": "Built a scheduling API", "github_url": "https://github.com/example/study-planner"}],
}
MARKDOWN = "# Invented Name\n\nincorrect@example.com\n\n## Summary\nBuilt reliable Python services.\n\n## Projects\n- **Study planner**: Built a scheduling API. [Source](https://github.com/example/study-planner)\n\n## Education\nBSc Computer Science."


def document():
    return build_resume_document(MARKDOWN, resume.ResumeGenerateRequest(**FACTS))


def client(authenticated=True):
    app = FastAPI()
    app.include_router(resume.router)
    if authenticated:
        app.dependency_overrides[resume.get_current_user] = lambda: {"id": "fixture-user"}
    return TestClient(app)


def test_document_uses_original_identity_and_contact_destinations():
    result = document()
    assert result.full_name == FACTS["full_name"]
    assert result.contacts[0].href == "mailto:alex@example.com"
    assert {contact.href for contact in result.contacts} >= {FACTS["github_url"], FACTS["linkedin_url"]}
    assert "my%20portfolio" in result.contacts[-1].href
    assert "incorrect@example.com" not in result.model_dump_json()
    assert [block.kind for block in result.blocks] == ["heading", "paragraph", "heading", "bullet", "heading", "paragraph"]


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "data:text/html,hi", "//example.com", "https://user:secret@example.com", "https://example.com\n/path", "https://example.com\\evil", "https://example.com:bad"])
def test_unsafe_urls_are_rejected(url):
    with pytest.raises(ValueError):
        normalize_web_url(url)
    with pytest.raises(ValidationError):
        ResumeSpan(text="Profile", href=url)


@pytest.mark.parametrize("field", ["github_url", "linkedin_url"])
def test_profile_fields_reject_app_url_and_lookalike_domains(field):
    for value in ["https://ai-placement-mentor-zo2w.onrender.com/resume", "https://github.com.evil.example", "https://linkedin.com.evil.example"]:
        with pytest.raises(ValidationError):
            resume.ResumeGenerateRequest(**{**FACTS, field: value})


def test_project_github_field_rejects_wrong_destination():
    with pytest.raises(ValidationError):
        resume.ProjectInput(title="Project", description="Description", github_url="https://example.com")


def test_unicode_and_query_links_are_encoded_without_losing_destination():
    assert normalize_web_url("https://example.com/café portfolio?q=a b&sort=new#my section") == "https://example.com/caf%C3%A9%20portfolio?q=a%20b&sort=new#my%20section"


def test_untrusted_markdown_cannot_add_active_invented_links_or_html():
    result = build_resume_document("## Summary\n<script>alert(1)</script> [Invented](https://evil.example) ![tracking](https://evil.example/track)\n", resume.ResumeGenerateRequest(**FACTS))
    active = {span.href for block in result.blocks for span in block.spans if span.href}
    assert "https://evil.example" not in active
    assert "https://evil.example/track" not in active
    assert FACTS["projects"][0]["github_url"] in active


def test_plain_supplied_project_urls_are_clickable():
    result = build_resume_document("## Projects\nSource: https://github.com/example/study-planner", resume.ResumeGenerateRequest(**FACTS))
    assert any(span.href == FACTS["projects"][0]["github_url"] for block in result.blocks for span in block.spans)
    assert not any(block.spans[0].text == "Project links" for block in result.blocks)


@pytest.mark.parametrize("markdown", ["", "# Resume", "# Name contact ## Summary the whole resume is one heading"])
def test_unformatted_writer_output_is_not_passed_off_as_a_complete_resume(markdown):
    with pytest.raises(ValueError, match="no formatted body"):
        build_resume_document(markdown, resume.ResumeGenerateRequest(**FACTS))


def test_pdf_contains_selectable_text_and_actual_link_annotations():
    pdf = render_resume_pdf(document())
    assert pdf.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "Alex Morgan" in text and "Built a scheduling API" in text
    assert "incorrect@example.com" not in text
    links = {annotation.get_object()["/A"]["/URI"] for page in reader.pages for annotation in page.get("/Annots", [])}
    assert {FACTS["github_url"], FACTS["linkedin_url"], FACTS["projects"][0]["github_url"], "mailto:alex@example.com"} <= links
    assert any("my%20portfolio" in value and "&language=Python" in value for value in links)


def test_long_pdf_paginates_without_discarding_content():
    content = document().model_dump()
    content["blocks"] = [{"kind": "paragraph", "spans": [{"text": f"Experience {index}: " + "Built reliable services. " * 18}]} for index in range(40)]
    reader = PdfReader(BytesIO(render_resume_pdf(ResumeDocument(**content))))
    assert len(reader.pages) > 1
    assert "Experience 39:" in "\n".join(page.extract_text() for page in reader.pages)


def test_pdf_escapes_untrusted_xml_instead_of_creating_extra_links():
    content = document().model_dump()
    content["blocks"] = [{"kind": "paragraph", "spans": [{"text": '<link href="https://evil.example">Fake</link> & <script>text</script>'}]}]
    reader = PdfReader(BytesIO(render_resume_pdf(ResumeDocument(**content))))
    assert '<link href="https://evil.example">' in reader.pages[0].extract_text()
    assert all(annotation.get_object()["/A"]["/URI"] != "https://evil.example" for annotation in reader.pages[0].get("/Annots", []))


def test_export_requires_authentication():
    with client(False) as app:
        assert app.post("/resume/export", json=document().model_dump()).status_code in {401, 403}


def test_export_response_is_pdf_attachment_without_cache_or_new_ai_call(monkeypatch):
    def no_ai(*args, **kwargs):
        pytest.fail("Export must not call an AI service")
    monkeypatch.setattr(resume.provider, "complete", no_ai)
    with client() as app:
        result = app.post("/resume/export", json=document().model_dump())
    assert result.status_code == 200
    assert result.headers["content-type"] == "application/pdf"
    assert result.headers["cache-control"] == "no-store"
    assert 'filename="resume.pdf"' in result.headers["content-disposition"]
    assert result.content.startswith(b"%PDF-")


def test_export_rejects_unsafe_links_and_oversized_documents():
    content = document().model_dump()
    with client() as app:
        unsafe = {**content, "contacts": [{"text": "Profile", "href": "javascript:alert(1)"}]}
        assert app.post("/resume/export", json=unsafe).status_code == 422
        oversized = {**content, "blocks": [{"kind": "paragraph", "spans": [{"text": "x" * 11000}]}] * 20}
        assert app.post("/resume/export", json=oversized).status_code == 422
