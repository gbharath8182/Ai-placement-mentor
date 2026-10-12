import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx


ROOT = Path(__file__).resolve().parents[1]


class LibraryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "div":
            if attributes.get("id") == "panel-books":
                self.depth = 1
            elif self.depth:
                self.depth += 1
        if tag == "a" and self.depth:
            self.current = {**attributes, "label": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["label"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.current["label"] = self.current["label"].strip()
            self.links.append(self.current)
            self.current = None
        if tag == "div" and self.depth:
            self.depth -= 1


def library_links():
    parser = LibraryParser()
    parser.feed((ROOT / "frontend" / "cheatsheets.html").read_text(encoding="utf-8"))
    return parser.links


def check_link(client, link):
    url = link["href"]
    result = {"url": url, "label": link["label"], "passed": False}
    if urlsplit(url).scheme != "https":
        return {**result, "kind": "https_required"}
    try:
        with client.stream("GET", url) as response:
            result.update(status=response.status_code, final_url=str(response.url))
            if not response.is_success or response.url.scheme != "https":
                return {**result, "kind": "http_status"}
            content_type = response.headers.get("content-type", "").split(";")[0]
            result["content_type"] = content_type
            if "pdf" in link["label"].lower() and content_type != "application/pdf":
                return {**result, "kind": "pdf_label_mismatch"}
            content = bytearray()
            budget = 4096 if content_type == "application/pdf" else 1024 * 1024
            for chunk in response.iter_bytes(chunk_size=4096):
                content.extend(chunk[:budget - len(content)])
                if len(content) >= budget:
                    break
            if content_type == "application/pdf":
                result["passed"] = content.startswith(b"%PDF-")
            elif content_type in {"text/html", "application/xhtml+xml"}:
                fragment = unquote(urlsplit(url).fragment)
                text = content.decode("utf-8", errors="replace")
                error_page = any(message in text.lower() for message in ["<title>something went wrong", "<title>404", "<title>access denied"])
                result["passed"] = bool(text.strip()) and not error_page and (
                    not fragment or any(attribute in text for attribute in (
                        f'id="{fragment}"', f"id='{fragment}'", f'name="{fragment}"', f"name='{fragment}'",
                    ))
                )
                if fragment and not result["passed"]:
                    result["kind"] = "fragment_missing"
            else:
                result["kind"] = "not_a_readable_document"
    except httpx.HTTPError:
        result["kind"] = "network"
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only checks for curated free-library links; never downloads or stores full books.")
    parser.parse_args()
    links = library_links()
    with httpx.Client(timeout=httpx.Timeout(20, connect=5), follow_redirects=True, max_redirects=5, trust_env=False) as client:
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(lambda link: check_link(client, link), links))
    for result in results:
        print(json.dumps(result))
    print(json.dumps({"check": "library_resources", "total": len(results), "passed": sum(result["passed"] for result in results)}))
    return 0 if results and all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
