import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC_SLUG = "python-strings-regex"

import sys
sys.path.insert(0, r"c:\Users\navaneeth\Ai-placement-mentor")
from backend.config import settings

async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]

    # Idempotent: safe to re-run without creating duplicates
    await db.topics.delete_many({"slug": TOPIC_SLUG})
    await db.practice_problems.delete_many({"topic_slug": TOPIC_SLUG})

    topic = {
        "domain_slug": "python",
        "slug": TOPIC_SLUG,
        "title": "Strings, Formatting \U0001F4DD Regular Expressions",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "String Fundamentals: Indexing, Slicing \U0001F5C2 Immutability",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Strings Are Immutable Sequences"},
                    {"type": "text", "value": "A Python string is an ordered, **immutable** sequence of characters. Immutable means that once a string is created, it can never be changed in place -- every 'modification' (`.upper()`, slicing, concatenation) actually builds and returns a brand new string object, leaving the original untouched. This is different from a list, where `.append()` mutates the same object in memory."},
                    {"type": "text", "value": "Because strings are sequences, you can index and slice them exactly like lists: `s[0]` gets the first character, `s[-1]` gets the last, and `s[start:stop:step]` extracts a substring."},
                    {"type": "list", "ordered": False, "items": [
                        "`s[2:5]` -- characters at index 2, 3, 4 (stop index is exclusive)",
                        "`s[:3]` -- first three characters",
                        "`s[3:]` -- everything from index 3 to the end",
                        "`s[::-1]` -- the entire string reversed (step of -1)",
                        "`s[-3:]` -- the last three characters"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Interview Trap: String Concatenation in a Loop", "value": "Writing `result = \"\"` then `result += word` inside a loop looks harmless but is **O(n^2)** overall, because each `+=` allocates an entirely new string and copies everything built so far. For building a string from many pieces, collect them in a list and call `\"\".join(pieces)` once at the end -- that's O(n)."},
                    {"type": "code", "language": "python", "value": "s = \"placement\"\nprint(s[0])       # 'p'\nprint(s[-1])      # 't'\nprint(s[2:5])     # 'ace'\nprint(s[::-1])    # 'tnemecalp'\n\n# Strings are immutable -- this creates a NEW string, it does not modify s\nshouted = s.upper()\nprint(s, shouted)  # placement PLACEMENT"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 6: Manipulating Strings", "url": "https://automatetheboringstuff.com/2e/chapter6/"}
                ]
            },
            {
                "title": "Essential String Methods \U0001F5C2 f-string Formatting",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "The Methods You Will Use Constantly"},
                    {"type": "text", "value": "Python strings ship with dozens of built-in methods for cleaning, splitting, and rebuilding text. In real automation and interview code, a small handful cover almost every case: `.strip()` to remove surrounding whitespace, `.split()` and `.join()` to move between a string and a list of pieces, `.replace()` for simple substitution, and `.startswith()` / `.endswith()` for prefix and suffix checks."},
                    {"type": "list", "ordered": False, "items": [
                        "`\"  hi  \".strip()` -> `\"hi\"` (also `.lstrip()` / `.rstrip()` for one side only)",
                        "`\"a,b,c\".split(\",\")` -> `[\"a\", \"b\", \"c\"]`",
                        "`\"-\".join([\"a\", \"b\", \"c\"])` -> `\"a-b-c\"`",
                        "`\"hello\".replace(\"l\", \"L\")` -> `\"heLLo\"`",
                        "`\"report.pdf\".endswith(\".pdf\")` -> `True`"
                    ]},
                    {"type": "callout", "kind": "info", "title": "f-string Format Spec Quick Reference", "value": "`{value:<10}` left-align in a 10-char field\\n`{value:>10}` right-align in a 10-char field\\n`{value:.2f}` fixed-point with 2 decimal places\\n`{value:,}` thousands separator\\n`{value:.1%}` show as a percentage with 1 decimal"},
                    {"type": "code", "language": "python", "value": "name = \"Alex\"\nscore = 87.5\n\n# Alignment and precision\nprint(f\"{name:<10}|{score:>8.2f}\")   # 'Alex      |   87.50'\n\n# Thousands separator and percentage\nprint(f\"{1234567:,}\")                # '1,234,567'\nprint(f\"{0.4567:.1%}\")               # '45.7%'\n\n# Method chaining is idiomatic Python\ncleaned = \"  Hello, World!  \".strip().lower()\nprint(cleaned)                        # 'hello, world!'"},
                    {"type": "resource_link", "label": "\U0001F4C4 Python Docs -- Format Specification Mini-Language", "url": "https://docs.python.org/3/library/string.html#format-specification-mini-language"}
                ]
            },
            {
                "title": "Regular Expressions Fundamentals: Matching Patterns",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Why Regex? Pattern Matching Beyond Exact Text"},
                    {"type": "text", "value": "String methods like `.replace()` only work with exact, known text. Regular expressions (regex), accessed through Python's `re` module, let you match *patterns* -- 'a sequence that looks like a phone number' or 'anything starting with a digit' -- rather than literal strings. This is essential for validating input, extracting structured data from messy text, and web scraping."},
                    {"type": "list", "ordered": False, "items": [
                        "`\\d` -- any digit, `\\D` -- any non-digit",
                        "`\\w` -- any word character (letter, digit, underscore), `\\W` -- the opposite",
                        "`\\s` -- any whitespace character",
                        "`+` -- one or more, `*` -- zero or more, `?` -- zero or one",
                        "`{3}` exactly 3 repeats, `{2,4}` between 2 and 4 repeats",
                        "`()` -- capturing group, `|` -- OR, `^` / `$` -- start / end of string"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "re.match vs re.search vs re.findall", "value": "`re.match()` only checks for a match at the **very start** of the string -- a common source of bugs when people expect it to behave like `.search()`. `re.search()` scans the whole string for the first match. `re.findall()` returns **every** non-overlapping match as a list. When in doubt, `re.search()` or `re.findall()` are usually what you actually want."},
                    {"type": "code", "language": "python", "value": "import re\n\ntext = \"Call 555-123-4567 or 800-555-0199\"\n\n# findall returns every match as a list of strings\nmatches = re.findall(r'\\d{3}-\\d{3}-\\d{4}', text)\nprint(matches)   # ['555-123-4567', '800-555-0199']\n\n# search returns the first Match object (or None)\nm = re.search(r'\\d{3}-\\d{3}-\\d{4}', text)\nif m:\n    print(m.group())   # '555-123-4567'"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 7: Pattern Matching with Regular Expressions", "url": "https://automatetheboringstuff.com/2e/chapter7/"},
                    {"type": "resource_link", "label": "\U0001F517 regex101.com -- Live Regex Tester \U0001F5C2 Debugger", "url": "https://regex101.com/"}
                ]
            },
            {
                "title": "Advanced Pattern Matching: Substitution, Greedy vs Non-Greedy \U0001F5C2 Named Groups",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Rewriting Text with re.sub()"},
                    {"type": "text", "value": "`re.sub(pattern, replacement, text)` finds every match of `pattern` in `text` and replaces it. The replacement can be a plain string, or -- far more powerfully -- a **function**, which receives the Match object for each hit and returns the string to substitute in its place. This lets you transform matched text based on its own content, not just stamp the same fixed string over every match."},
                    {"type": "list", "ordered": False, "items": [
                        "Greedy (`.*`, default): matches as **much** text as possible -- can over-match across multiple intended targets",
                        "Non-greedy / lazy (`.*?`): matches as **little** text as possible -- usually what you want when scanning tags or delimiters",
                        "Named groups `(?P<name>...)`: capture a group and reference it by name via `.group(\"name\")` instead of a numeric index",
                        "`re.compile(pattern)` pre-compiles a pattern once for reuse -- worth doing when the same regex runs inside a loop over many lines"
                    ]},
                    {"type": "callout", "kind": "important", "title": "Watch Out for Catastrophic Backtracking", "value": "Certain regex patterns -- typically nested quantifiers like `(a+)+` -- can cause the regex engine's backtracking to blow up exponentially on specially-crafted input, freezing your program. This is a real, documented class of bug (and denial-of-service vector, sometimes called ReDoS) in production systems, not just a theoretical curiosity. Keep patterns as simple and specific as the problem allows, and be wary of stacking multiple `+`/`*` quantifiers around the same sub-pattern."},
                    {"type": "code", "language": "python", "value": "import re\n\n# Greedy vs non-greedy on HTML-like tags\nhtml = \"<b>bold</b> and <i>italic</i>\"\nprint(re.findall(r'<.*>', html))    # greedy: ['<b>bold</b> and <i>italic</i>']\nprint(re.findall(r'<.*?>', html))   # lazy:   ['<b>', '</b>', '<i>', '</i>']\n\n# Named groups\nm = re.search(r'(?P<area>\\d{3})-(?P<mid>\\d{3})-(?P<last>\\d{4})', \"Call 415-555-1234\")\nprint(m.group(\"area\"), m.group(\"mid\"), m.group(\"last\"))   # 415 555 1234\n\n# re.sub with a function -- mask each matched email\ndef mask(match):\n    local, domain = match.group(0).split(\"@\", 1)\n    return local[0] + \"***@\" + domain\n\ntext = \"Contact john.doe@example.com or admin@test.org\"\nprint(re.sub(r'\\b[\\w.+-]+@[\\w.-]+\\.\\w+\\b', mask, text))"},
                    {"type": "resource_link", "label": "\U0001F4C4 Python Docs -- re module (Full Reference)", "url": "https://docs.python.org/3/library/re.html"}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print(f"Inserted topic '{TOPIC_SLUG}' -> _id={result.inserted_id}")

    problems = [
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Reverse Word Order in a Sentence",
            "difficulty": "easy",
            "description": "Read a line of text from stdin. Print the words in reverse order (the last word first), separated by single spaces. Use string splitting and joining, not manual character manipulation.\n\nExample:\nInput: the quick brown fox\nOutput: fox brown quick the",
            "starter_code": "# Read the line\nline = input()\n\n# Split into words, reverse the order, and rejoin\nwords = line.split()\nprint(\" \".join(reversed(words)))\n",
            "test_cases": [
                {"input": "the quick brown fox", "expected_output": "fox brown quick the"},
                {"input": "hello", "expected_output": "hello"},
                {"input": "  padded   spacing   here  ", "expected_output": "here spacing padded"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Extract Phone Numbers with Regex",
            "difficulty": "medium",
            "description": "Read a line of text from stdin that may contain zero or more phone numbers in the exact format XXX-XXX-XXXX. Print all matches found, in order, separated by a single space. If none are found, print NONE.\n\nExample:\nInput: Call me at 555-123-4567 or 800-555-0199 tomorrow\nOutput: 555-123-4567 800-555-0199",
            "starter_code": "import re\n\ntext = input()\n\n# Find every XXX-XXX-XXXX pattern\nmatches = re.findall(r'\\d{3}-\\d{3}-\\d{4}', text)\nprint(\" \".join(matches) if matches else \"NONE\")\n",
            "test_cases": [
                {"input": "Call me at 555-123-4567 or 800-555-0199 tomorrow", "expected_output": "555-123-4567 800-555-0199"},
                {"input": "No numbers here at all", "expected_output": "NONE"},
                {"input": "Contact: 123-456-7890", "expected_output": "123-456-7890"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Mask Email Addresses",
            "difficulty": "hard",
            "description": "Read a line of text from stdin containing zero or more email addresses. Replace every email address with a masked version: the first character of the local part, followed by ***@ and the full domain unchanged. Print the resulting line. Use re.sub with a replacement function.\n\nExample:\nInput: Contact john.doe@example.com or admin@test.org for help\nOutput: Contact j***@example.com or a***@test.org for help",
            "starter_code": "import re\n\ndef mask(match):\n    local, domain = match.group(0).split(\"@\", 1)\n    return local[0] + \"***@\" + domain\n\ntext = input()\nresult = re.sub(r'\\b[\\w.+-]+@[\\w.-]+\\.\\w+\\b', mask, text)\nprint(result)\n",
            "test_cases": [
                {"input": "Contact john.doe@example.com or admin@test.org for help", "expected_output": "Contact j***@example.com or a***@test.org for help"},
                {"input": "No emails in this line", "expected_output": "No emails in this line"},
                {"input": "Reach a@b.co now", "expected_output": "Reach a***@b.co now"}
            ]
        }
    ]

    result = await db.practice_problems.insert_many(problems)
    print(f"Inserted {len(result.inserted_ids)} practice problems for '{TOPIC_SLUG}'")

asyncio.run(main())
