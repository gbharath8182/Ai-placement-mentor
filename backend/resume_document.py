import re
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote, urlsplit, urlunsplit

import reportlab
from markdown_it import MarkdownIt
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def normalize_web_url(value: str, domain: str = "") -> str:
    if not value:
        return ""
    if any(ord(character) < 32 for character in value) or "\\" in value:
        raise ValueError("Use a complete HTTP or HTTPS URL without control characters")
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Use a complete HTTP or HTTPS URL")
    hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    if domain and hostname not in {domain, "www." + domain}:
        raise ValueError(f"Use your actual {domain} profile or repository URL")
    port = parsed.port
    host = f"[{hostname}]" if ":" in hostname else hostname
    if port:
        host += f":{port}"
    return urlunsplit((parsed.scheme.lower(), host, quote(parsed.path, safe="/%:@-._~!$&'()*+,;="),
                      quote(parsed.query, safe="%=&/?@-._~!$'()*+,;:"), quote(parsed.fragment, safe="%/?@-._~!$&'()*+,;=:")))


class ResumeSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: Annotated[str, Field(min_length=1, max_length=12000)]
    bold: bool = False
    href: Annotated[str, Field(max_length=1500)] = ""

    @field_validator("href")
    @classmethod
    def safe_href(cls, value):
        if value.startswith("mailto:"):
            if not re.fullmatch(r"mailto:[A-Za-z0-9.!#$%&'*+/=^_`{|}~-]+@[A-Za-z0-9.-]+", value):
                raise ValueError("Invalid email link")
            return value
        return normalize_web_url(value)


class ResumeBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["heading", "subheading", "paragraph", "bullet"]
    spans: Annotated[list[ResumeSpan], Field(min_length=1, max_length=150)]


class ResumeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    full_name: Annotated[str, Field(min_length=1, max_length=200)]
    target_role: Annotated[str, Field(max_length=200)] = ""
    contacts: Annotated[list[ResumeSpan], Field(max_length=8)] = Field(default_factory=list)
    blocks: Annotated[list[ResumeBlock], Field(min_length=1, max_length=200)]

    @model_validator(mode="after")
    def bounded_size(self):
        if len(self.model_dump_json()) > 100000:
            raise ValueError("Resume document exceeds the export limit")
        return self


def inline_spans(tokens, allowed_links):
    spans = []
    bold = False
    href = ""
    for token in tokens:
        if token.type == "strong_open":
            bold = True
        elif token.type == "strong_close":
            bold = False
        elif token.type == "link_open":
            try:
                destination = normalize_web_url(token.attrGet("href") or "")
            except ValueError:
                destination = ""
            href = destination if destination in allowed_links else ""
        elif token.type == "link_close":
            href = ""
        elif token.type in {"text", "code_inline", "softbreak", "hardbreak"}:
            content = " " if token.type.endswith("break") else token.content
            for part in re.split(r"(https?://[^\s<>]+)", content):
                if not part:
                    continue
                destination = href
                if not href and part.startswith(("http://", "https://")):
                    try:
                        candidate = normalize_web_url(part.rstrip(".,;"))
                        destination = candidate if candidate in allowed_links else ""
                    except ValueError:
                        pass
                spans.append(ResumeSpan(text=part, bold=bold, href=destination))
    return spans


def build_resume_document(markdown, facts):
    if not isinstance(markdown, str) or len(markdown) > 60000:
        raise ValueError("Resume content exceeds the supported size")
    contacts = []
    for field in ("email", "phone", "location"):
        if getattr(facts, field):
            destination = "mailto:" + facts.email if field == "email" else ""
            contacts.append(ResumeSpan(text=getattr(facts, field), href=destination))
    for field, label in (("github_url", "GitHub"), ("linkedin_url", "LinkedIn"), ("portfolio_url", "Portfolio")):
        if getattr(facts, field):
            contacts.append(ResumeSpan(text=label, href=getattr(facts, field)))
    project_links = [(project.title, label, getattr(project, field)) for project in facts.projects
                     for field, label in (("github_url", "Source"), ("live_url", "Live demo")) if getattr(project, field)]
    allowed_links = {contact.href for contact in contacts if contact.href}
    allowed_links.update(destination for title, label, destination in project_links)
    tokens = MarkdownIt("commonmark", {"html": False}).parse(markdown)
    has_sections = any(token.type == "heading_open" and token.tag == "h2" for token in tokens)
    started = not has_sections
    heading = ""
    list_depth = 0
    blocks = []
    for token in tokens:
        if token.type == "heading_open":
            heading = token.tag
            if token.tag == "h2":
                started = True
        elif token.type == "heading_close":
            heading = ""
        elif token.type == "list_item_open":
            list_depth += 1
        elif token.type == "list_item_close":
            list_depth -= 1
        elif token.type == "inline" and started and heading != "h1":
            spans = inline_spans(token.children or [], allowed_links)
            if spans:
                kind = "heading" if heading == "h2" else "subheading" if heading else "bullet" if list_depth else "paragraph"
                blocks.append(ResumeBlock(kind=kind, spans=spans))
    if not blocks:
        raise ValueError("The generated resume has no formatted body")
    present_links = {span.href for block in blocks for span in block.spans if span.href}
    missing_links = [(title, label, destination) for title, label, destination in project_links if destination not in present_links]
    if missing_links:
        blocks.append(ResumeBlock(kind="heading", spans=[ResumeSpan(text="Project links")]))
        for title, label, destination in missing_links:
            blocks.append(ResumeBlock(kind="paragraph", spans=[ResumeSpan(text=title + " / " + label, href=destination)]))
    return ResumeDocument(full_name=facts.full_name, target_role=facts.target_role, contacts=contacts, blocks=blocks)


def paragraph_markup(spans):
    pieces = []
    for span in spans:
        content = escape(span.text).replace("\n", "<br/>")
        if span.bold:
            content = "<b>" + content + "</b>"
        if span.href:
            content = '<link href="' + escape(span.href, quote=True) + '" color="#28475C">' + content + "</link>"
        pieces.append(content)
    return "".join(pieces)


def render_resume_pdf(document):
    font_directory = Path(reportlab.__file__).parent / "fonts"
    if "ResumeSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("ResumeSans", str(font_directory / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("ResumeSans-Bold", str(font_directory / "VeraBd.ttf")))
        pdfmetrics.registerFontFamily("ResumeSans", normal="ResumeSans", bold="ResumeSans-Bold", italic="ResumeSans", boldItalic="ResumeSans-Bold")
    output = BytesIO()
    styles = {
        "name": ParagraphStyle("name", fontName="ResumeSans-Bold", fontSize=22, leading=27, alignment=TA_CENTER, spaceAfter=5),
        "role": ParagraphStyle("role", fontName="ResumeSans", fontSize=10.5, leading=15, alignment=TA_CENTER, spaceAfter=5),
        "contacts": ParagraphStyle("contacts", fontName="ResumeSans", fontSize=8.7, leading=13, alignment=TA_CENTER, spaceAfter=4),
        "heading": ParagraphStyle("heading", fontName="ResumeSans-Bold", fontSize=10, leading=14, spaceBefore=14, spaceAfter=4, keepWithNext=True),
        "subheading": ParagraphStyle("subheading", fontName="ResumeSans-Bold", fontSize=10, leading=15, spaceBefore=6, spaceAfter=4, keepWithNext=True),
        "paragraph": ParagraphStyle("paragraph", fontName="ResumeSans", fontSize=9.5, leading=14, spaceAfter=5, splitLongWords=True),
        "bullet": ParagraphStyle("bullet", fontName="ResumeSans", fontSize=9.5, leading=14, leftIndent=11, firstLineIndent=0, bulletIndent=0, spaceAfter=4),
    }
    story = [Paragraph(escape(document.full_name), styles["name"])]
    if document.target_role:
        story.append(Paragraph(escape(document.target_role), styles["role"]))
    if document.contacts:
        story.append(Paragraph(" &nbsp; | &nbsp; ".join(paragraph_markup([contact]) for contact in document.contacts), styles["contacts"]))
    story.append(Spacer(1, 4))
    for block in document.blocks:
        content = escape("".join(span.text for span in block.spans).upper()) if block.kind == "heading" else paragraph_markup(block.spans)
        story.append(Paragraph(content, styles[block.kind], bulletText="•" if block.kind == "bullet" else None))
        if block.kind == "heading":
            rule = HRFlowable(width="100%", thickness=.4, color=colors.HexColor("#D7DCE0"), spaceAfter=6)
            rule.keepWithNext = True
            story.append(rule)

    def page_footer(canvas, template):
        canvas.saveState()
        canvas.setFont("ResumeSans", 7)
        canvas.setFillColor(colors.HexColor("#64717A"))
        canvas.drawRightString(A4[0] - 42, 23, str(template.page))
        canvas.restoreState()

    template = SimpleDocTemplate(output, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=38, bottomMargin=38,
                                 title=document.full_name + " - Resume", author=document.full_name)
    template.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return output.getvalue()
