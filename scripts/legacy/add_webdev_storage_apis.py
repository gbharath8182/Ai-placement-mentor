import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC_SLUG = "web-storage-apis"

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    await db.topics.delete_many({"slug": TOPIC_SLUG})
    await db.practice_problems.delete_many({"topic_slug": TOPIC_SLUG})

    topic = {
        "domain_slug": "web-dev",
        "slug": TOPIC_SLUG,
        "title": "Web APIs: JSON, Browser Storage & Fetch",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Working with JSON in JavaScript",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Converting Between Objects and JSON Text"},
                    {"type": "text", "value": "JSON.stringify() and JSON.parse() are the two functions that move data between a live JavaScript object and its JSON text representation. This conversion is required constantly -- every time data is sent to a server, saved to browser storage, or received from an API, it travels as a JSON string."},
                    {"type": "list", "ordered": False, "items": [
                        "`JSON.stringify(obj)` -- object/array -> JSON string",
                        "`JSON.parse(text)` -- JSON string -> object/array",
                        "`JSON.stringify(obj, null, 2)` -- pretty-printed with 2-space indentation, useful for debugging",
                        "Functions, `undefined`, and circular references cannot be represented in JSON -- `JSON.stringify` silently drops or errors on them"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "parse() Throws on Invalid JSON", "value": "`JSON.parse()` throws a `SyntaxError` if given text that isn't valid JSON -- a single trailing comma or unquoted key will break it. When parsing anything from an external source (an API response, user input, storage), wrap the call in `try/catch` rather than assuming it will always succeed."},
                    {"type": "code", "language": "javascript", "value": "const obj = { b: 2, a: 1, c: 3 };\nconst json = JSON.stringify(obj);\nconsole.log(json);                        // {\"b\":2,\"a\":1,\"c\":3}\n\nconst parsed = JSON.parse(json);\nconsole.log(Object.keys(parsed).sort());  // [ 'a', 'b', 'c' ]\n\ntry {\n  JSON.parse(\"{ invalid json }\");\n} catch (err) {\n  console.error(\"Bad JSON:\", err.message);\n}"},
                    {"type": "resource_link", "label": "\U0001F4C4 MDN -- JSON.stringify()", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify"}
                ]
            },
            {
                "title": "Browser Storage: localStorage & sessionStorage",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Persisting Data in the Browser"},
                    {"type": "text", "value": "`localStorage` and `sessionStorage` are simple key-value stores built into every browser. `localStorage` persists until explicitly cleared -- it survives closing the tab or the browser entirely. `sessionStorage` is scoped to a single tab's lifetime and is cleared as soon as that tab closes. Both only store strings, so non-string data must go through `JSON.stringify`/`parse` to round-trip correctly."},
                    {"type": "list", "ordered": False, "items": [
                        "`localStorage.setItem(key, value)` / `.getItem(key)` / `.removeItem(key)`",
                        "`sessionStorage` has the identical API, just a shorter lifetime",
                        "Both are synchronous and origin-scoped -- a page can only read storage it set itself, not another site's",
                        "Typical size limit is around 5-10MB per origin, browser-dependent -- not suitable for large datasets"
                    ]},
                    {"type": "callout", "kind": "important", "title": "Storage Only Holds Strings", "value": "`localStorage.setItem(\"user\", {name: \"Alex\"})` silently stores the string `\"[object Object]\"`, not the object -- a very common and confusing bug. Always explicitly `JSON.stringify()` before storing an object, and `JSON.parse()` after retrieving it."},
                    {"type": "code", "language": "javascript", "value": "// Storing and retrieving a simple string\nlocalStorage.setItem(\"theme\", \"dark\");\nconsole.log(localStorage.getItem(\"theme\"));   // dark\nlocalStorage.removeItem(\"theme\");\n\n// Storing an object requires JSON.stringify / parse\nconst user = { name: \"Alex\", loggedIn: true };\nlocalStorage.setItem(\"user\", JSON.stringify(user));\nconst restored = JSON.parse(localStorage.getItem(\"user\"));\nconsole.log(restored.name);   // Alex"},
                    {"type": "resource_link", "label": "\U0001F4C4 MDN -- Window.localStorage", "url": "https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage"}
                ]
            },
            {
                "title": "The Fetch API: Making HTTP Requests",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Calling APIs from the Browser"},
                    {"type": "text", "value": "`fetch(url)` sends an HTTP request and returns a Promise that resolves to a Response object once the headers arrive (the body may still be streaming). This connects directly to the async/await material already covered: fetch is the canonical real-world use case for `await`, since a network request is inherently asynchronous."},
                    {"type": "list", "ordered": False, "items": [
                        "`const res = await fetch(url);` -- resolves once headers are received",
                        "`res.ok` -- boolean, true for any 2xx status; `res.status` -- the numeric status code",
                        "`await res.json()` -- parses the body as JSON (also returns a Promise, since the body streams in)",
                        "`fetch(url, { method: \"POST\", headers: {...}, body: JSON.stringify(data) })` -- sending data, not just requesting it"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "fetch() Does Not Reject on HTTP Errors", "value": "A 404 or 500 response does not make the returned Promise reject -- `fetch` only rejects for network-level failures (DNS failure, no connection). A 404 page still resolves successfully with `res.ok === false`. Always check `res.ok` (or `res.status`) explicitly before trusting the response, the same lesson as `requests.raise_for_status()` on the Python side."},
                    {"type": "code", "language": "javascript", "value": "async function getUser(id) {\n  const res = await fetch(`/api/users/${id}`);\n  if (!res.ok) {\n    throw new Error(`Request failed: ${res.status}`);\n  }\n  return res.json();\n}\n\ngetUser(42)\n  .then(user => console.log(user.name))\n  .catch(err => console.error(err.message));"},
                    {"type": "resource_link", "label": "\U0001F4C4 MDN -- Using the Fetch API", "url": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch"}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print(f"Inserted topic '{TOPIC_SLUG}' -> _id={result.inserted_id}")

    # Note: only JSON.stringify/parse logic is graded here -- it's synchronous and
    # deterministic. localStorage and fetch are illustrative-only in this topic
    # because the test harness executes code with new Function(code)() and does not
    # await Promises/microtasks before checking output, so real async timing can't
    # be reliably graded. Same design constraint as NP-Completeness having zero
    # graded problems -- documented, not an oversight.
    problems = [
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Sort and Print Object Keys",
            "difficulty": "easy",
            "description": "Read a JSON object using prompt(). Print its keys, sorted alphabetically, comma-separated with no spaces.\n\nExample:\nInput: {\"b\": 2, \"a\": 1, \"c\": 3}\nOutput: a,b,c",
            "starter_code": "const raw = prompt();\nconst obj = JSON.parse(raw);\nconst keys = Object.keys(obj).sort();\nconsole.log(keys.join(\",\"));\n",
            "test_cases": [
                {"input": "{\"b\": 2, \"a\": 1, \"c\": 3}", "expected_output": "a,b,c"},
                {"input": "{\"z\": 1}", "expected_output": "z"},
                {"input": "{\"name\": 1, \"age\": 2, \"city\": 3}", "expected_output": "age,city,name"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Calculate Cart Total from JSON",
            "difficulty": "medium",
            "description": "Read a JSON array of items using prompt(), each with a 'price' and 'qty' field. Print the total cost (price * qty summed across all items), formatted to 2 decimal places.\n\nExample:\nInput: [{\"price\": 10, \"qty\": 2}, {\"price\": 5.5, \"qty\": 3}]\nOutput: 36.50",
            "starter_code": "const raw = prompt();\nconst items = JSON.parse(raw);\nconst total = items.reduce((sum, item) => sum + item.price * item.qty, 0);\nconsole.log(total.toFixed(2));\n",
            "test_cases": [
                {"input": "[{\"price\": 10, \"qty\": 2}, {\"price\": 5.5, \"qty\": 3}]", "expected_output": "36.50"},
                {"input": "[{\"price\": 100, \"qty\": 1}]", "expected_output": "100.00"},
                {"input": "[{\"price\": 1, \"qty\": 1}, {\"price\": 1, \"qty\": 1}]", "expected_output": "2.00"}
            ]
        }
    ]

    result = await db.practice_problems.insert_many(problems)
    print(f"Inserted {len(result.inserted_ids)} practice problems for '{TOPIC_SLUG}'")

asyncio.run(main())
