import httpx

from scripts.check_resources import LibraryParser, check_link, library_links


def test_library_has_twelve_safe_direct_free_reading_links():
    links = library_links()
    assert len(links) == 12
    assert len({link["href"] for link in links}) == 12
    for link in links:
        assert link["href"].startswith("https://")
        assert link["target"] == "_blank"
        assert {"noopener", "noreferrer"} <= set(link["rel"].split())
        assert any(label in link["label"].lower() for label in ["free", "reading"])
        assert not any(host in link["href"] for host in ["mheducation.com", "db-book.com", "dataintensive.net", "amazon.com", "kurose_ross"])


def test_parser_excludes_other_panels_and_handles_nested_cards():
    parser = LibraryParser()
    parser.feed('<a href="https://ignored.example">Before</a><div id="panel-books"><div><div>Card</div><a href="https://reading.example">Free chapters</a></div></div><a href="https://ignored.example">After</a>')
    assert [(link["href"], link["label"]) for link in parser.links] == [("https://reading.example", "Free chapters")]


def test_checker_validates_pdf_signature_and_html_fragments():
    for content, kind, fragment, passed in [
        (b"%PDF-1.7 trusted document", "application/pdf", "", True),
        (b"not a PDF", "application/pdf", "", False),
        (b'<html><section id="chapters">Text</section></html>', "text/html", "#chapters", True),
        (b"<html>Landing page</html>", "text/html", "#chapters", False),
        (b"<html>Free chapter</html>", "text/html", "", True),
    ]:
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content, headers={"content-type": kind}))) as client:
            assert check_link(client, {"href": "https://author.example/book" + fragment, "label": "Read free"})["passed"] is passed


def test_checker_reports_failures_without_remote_response_text():
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(403, text="private rejection"))) as client:
        result = check_link(client, {"href": "https://author.example/book", "label": "Read free"})
        assert result["passed"] is False
        assert result["status"] == 403
        assert "private rejection" not in str(result)


def test_pdf_label_rejects_html_even_when_status_is_success():
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, text="<html>Security rejection</html>", headers={"content-type": "text/html"}))) as client:
        result = check_link(client, {"href": "https://author.example/book.pdf", "label": "Open free PDF"})
        assert result["passed"] is False
        assert result["kind"] == "pdf_label_mismatch"
