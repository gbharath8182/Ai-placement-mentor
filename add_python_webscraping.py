import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC_SLUG = "python-web-scraping"

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    await db.topics.delete_many({"slug": TOPIC_SLUG})
    await db.practice_problems.delete_many({"topic_slug": TOPIC_SLUG})

    topic = {
        "domain_slug": "python",
        "slug": TOPIC_SLUG,
        "title": "Web Scraping Fundamentals",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "The webbrowser Module: Launching URLs from Code",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Automating a Simple Browser Action"},
                    {"type": "text", "value": "The `webbrowser` module is the simplest possible starting point for web automation: it opens a URL in the user's default browser directly from a Python script, with no downloading or parsing involved. It's commonly used to quickly build a script that turns a piece of text -- an address, a search term -- into a one-click browser action."},
                    {"type": "list", "ordered": False, "items": [
                        "`webbrowser.open(url)` -- opens the given URL in a new browser tab",
                        "Useful for small productivity scripts: e.g. select an address, run a script, get a map instantly",
                        "Does not download or return any page content -- purely launches the browser"
                    ]},
                    {"type": "callout", "kind": "info", "title": "Why Start Here", "value": "webbrowser.open() has no error handling to worry about and no HTML to parse -- it's a good first script for getting comfortable with the idea of code driving a browser, before moving into requests and BeautifulSoup which do real content extraction."},
                    {"type": "code", "language": "python", "value": "import webbrowser\n\naddress = \"1600 Amphitheatre Parkway\"\nurl = \"https://www.google.com/maps/place/\" + address.replace(\" \", \"+\")\nwebbrowser.open(url)"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 11: Web Scraping", "url": "https://automatetheboringstuff.com/2e/chapter11/"}
                ]
            },
            {
                "title": "Downloading Web Content with requests",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Fetching Pages and Files Over HTTP"},
                    {"type": "text", "value": "The third-party `requests` library is the standard way to download content from the web in Python. `requests.get(url)` sends an HTTP GET request and returns a `Response` object holding the status code, headers, and body content."},
                    {"type": "list", "ordered": False, "items": [
                        "`response.status_code` -- e.g. 200 (success), 404 (not found), 500 (server error)",
                        "`response.raise_for_status()` -- raises an exception if the request failed, instead of silently continuing with bad data",
                        "`response.text` -- body content decoded as a string (for HTML/JSON pages)",
                        "`response.content` -- body content as raw bytes (for binary files like PDFs or images)"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "Always Call raise_for_status()", "value": "requests does **not** raise an exception on its own for a 404 or 500 response -- it happily returns a Response object either way, and code that assumes success without checking will silently process an error page as if it were real data. Calling `response.raise_for_status()` immediately after every `requests.get()` catches this early."},
                    {"type": "code", "language": "python", "value": "import requests\n\nresponse = requests.get(\"https://example.com/report.pdf\")\nresponse.raise_for_status()   # stop here if the download failed\n\nwith open(\"report.pdf\", \"wb\") as f:\n    f.write(response.content)   # binary content -> write mode 'wb'"},
                    {"type": "resource_link", "label": "\U0001F4C4 requests Library -- Official Documentation", "url": "https://requests.readthedocs.io/en/latest/"}
                ]
            },
            {
                "title": "Parsing HTML with BeautifulSoup",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Turning Raw HTML into Searchable Structure"},
                    {"type": "text", "value": "Downloaded HTML is just one long string -- `BeautifulSoup` parses that string into a navigable tree of tags, so you can search for elements by tag name, CSS class, id, or a full CSS selector instead of manually hunting through text."},
                    {"type": "list", "ordered": False, "items": [
                        "`BeautifulSoup(html_text, \"html.parser\")` -- parse a string of HTML into a soup object",
                        "`soup.find(\"h1\", class_=\"title\")` -- first matching element",
                        "`soup.find_all(\"a\")` -- every matching element, as a list",
                        "`soup.select(\"div.article > a.nav-link\")` -- full CSS selector support",
                        "`.get_text()` -- visible text inside a tag; `.get(\"href\")` -- an attribute's value"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Prefer .select() for Complex Targets", "value": "For anything beyond a single tag name and class, `soup.select(\"...\")` with a real CSS selector is usually clearer and more precise than chaining multiple `.find()` calls -- especially if you already know CSS from front-end work."},
                    {"type": "code", "language": "python", "value": "from bs4 import BeautifulSoup\n\nhtml_doc = \"<html><body><h1 class='title'>Hello</h1></body></html>\"\nsoup = BeautifulSoup(html_doc, \"html.parser\")\n\nheading = soup.find(\"h1\", class_=\"title\")\nprint(heading.get_text())   # Hello\n\nfor link in soup.select(\"a.nav-link\"):\n    print(link.get(\"href\"))"},
                    {"type": "resource_link", "label": "\U0001F4C4 BeautifulSoup -- Official Documentation", "url": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/"}
                ]
            },
            {
                "title": "Being a Good Scraping Citizen: robots.txt, Rate Limiting & Ethics",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Scraping Responsibly"},
                    {"type": "text", "value": "A working scraper is not automatically a legal or ethical one. Most sites publish a `/robots.txt` file stating which paths automated tools are and are not allowed to access, and many sites' Terms of Service explicitly restrict scraping. Beyond the legal question, hammering a server with rapid-fire requests can degrade it for real users or get your IP address blocked."},
                    {"type": "list", "ordered": False, "items": [
                        "Check `https://sitename.com/robots.txt` before scraping and respect `Disallow` rules",
                        "Add a delay between requests with `time.sleep(...)` rather than firing them as fast as possible",
                        "Send a real `User-Agent` header identifying your script, not a spoofed browser string pretending to be human traffic",
                        "Prefer a site's official API over scraping its HTML, if one exists -- it's more stable and explicitly sanctioned"
                    ]},
                    {"type": "callout", "kind": "important", "title": "This Is Not Optional Politeness", "value": "Scraping in violation of a site's Terms of Service or robots.txt can have real legal consequences depending on jurisdiction and how the data is used, separate from any technical block. Treat 'is this actually allowed here' as a required step before writing the scraper, not an afterthought once it works."},
                    {"type": "code", "language": "python", "value": "import time\n\nurls = [\"https://example.com/page1\", \"https://example.com/page2\", \"https://example.com/page3\"]\n\nfor url in urls:\n    print(f\"Fetching {url}\")\n    # response = requests.get(url, headers={\"User-Agent\": \"MyPlacementBot/1.0\"})\n    time.sleep(1)   # be a polite crawler -- don't hammer the server"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 12: Web Scraping with BeautifulSoup", "url": "https://automatetheboringstuff.com/2e/chapter12/"}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print(f"Inserted topic '{TOPIC_SLUG}' -> _id={result.inserted_id}")

    problems = [
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Extract Page Title from HTML",
            "difficulty": "easy",
            "description": "Read one line of raw HTML from stdin (simulating a downloaded page). Extract and print the text inside the <title>...</title> tag. If there is no title tag, print NO TITLE.\n\nNote: this uses a string of HTML as input rather than a live network request, since the code sandbox has no internet access -- the parsing logic is identical to what you'd run on a real response.text.\n\nExample:\nInput: <html><head><title>Placement Mentor - Home</title></head></html>\nOutput: Placement Mentor - Home",
            "starter_code": "import re\n\nhtml = input()\nm = re.search(r'<title>(.*?)</title>', html)\nprint(m.group(1) if m else \"NO TITLE\")\n",
            "test_cases": [
                {"input": "<html><head><title>Placement Mentor - Home</title></head><body></body></html>", "expected_output": "Placement Mentor - Home"},
                {"input": "<html><head></head><body>No title here</body></html>", "expected_output": "NO TITLE"},
                {"input": "<title>Simple Page</title>", "expected_output": "Simple Page"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Count Links on a Page",
            "difficulty": "easy",
            "description": "Read one line of raw HTML from stdin. Count and print how many anchor tags (<a href=...>) appear in it.\n\nExample:\nInput: <a href=\"/home\">Home</a> <a href=\"/about\">About</a> <p>text</p> <a href=\"/contact\">Contact</a>\nOutput: 3",
            "starter_code": "import re\n\nhtml = input()\nlinks = re.findall(r'<a\\s+href=', html)\nprint(len(links))\n",
            "test_cases": [
                {"input": "<a href=\"/home\">Home</a> <a href=\"/about\">About</a> <p>text</p> <a href=\"/contact\">Contact</a>", "expected_output": "3"},
                {"input": "<p>No links on this page</p>", "expected_output": "0"},
                {"input": "<a href=\"/x\">X</a>", "expected_output": "1"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Extract All href URLs",
            "difficulty": "medium",
            "description": "Read one line of raw HTML from stdin. Extract every URL found inside an href=\"...\" attribute and print them in order, separated by single spaces. If none are found, print NONE.\n\nExample:\nInput: <a href=\"/home\">Home</a> <a href=\"https://example.com\">Ex</a>\nOutput: /home https://example.com",
            "starter_code": "import re\n\nhtml = input()\nurls = re.findall(r'href=\"([^\"]*)\"', html)\nprint(\" \".join(urls) if urls else \"NONE\")\n",
            "test_cases": [
                {"input": "<a href=\"/home\">Home</a> <a href=\"https://example.com\">Ex</a>", "expected_output": "/home https://example.com"},
                {"input": "<p>No links here</p>", "expected_output": "NONE"},
                {"input": "<a href=\"/only\">Only</a>", "expected_output": "/only"}
            ]
        }
    ]

    result = await db.practice_problems.insert_many(problems)
    print(f"Inserted {len(result.inserted_ids)} practice problems for '{TOPIC_SLUG}'")

asyncio.run(main())
