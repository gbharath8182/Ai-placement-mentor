import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC_SLUG = "python-excel-csv-json"

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    await db.topics.delete_many({"slug": TOPIC_SLUG})
    await db.practice_problems.delete_many({"topic_slug": TOPIC_SLUG})

    topic = {
        "domain_slug": "python",
        "slug": TOPIC_SLUG,
        "title": "Working with Excel, CSV & JSON Data",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Reading & Writing Excel Spreadsheets with openpyxl",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Automating Spreadsheet Work"},
                    {"type": "text", "value": "The `openpyxl` library reads and writes `.xlsx` files directly from Python, without needing Excel installed. This is genuinely one of the most useful real-world automation skills -- turning a manual 'open the spreadsheet, copy some numbers, update a report' task into a script that runs in seconds."},
                    {"type": "list", "ordered": False, "items": [
                        "`Workbook()` -- create a new spreadsheet in memory; `wb.active` -- the default sheet",
                        "`sheet[\"A1\"] = value` -- set a cell by its reference; `sheet.append([...])` -- add a full row at once",
                        "`load_workbook(path)` -- open an existing .xlsx file",
                        "`sheet.iter_rows(min_row=2, values_only=True)` -- iterate rows as plain tuples, skipping a header row",
                        "`wb.save(path)` -- write changes to disk (nothing is saved until this is called)"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Rows and Columns Are 1-Indexed, Not 0-Indexed", "value": "Unlike Python lists, openpyxl's row and column numbers start at 1, matching how Excel itself labels them (row 1, column A = column 1). Mixing this up with 0-indexed Python habits is a very common off-by-one bug when working with cell coordinates directly."},
                    {"type": "code", "language": "python", "value": "from openpyxl import Workbook, load_workbook\n\nwb = Workbook()\nsheet = wb.active\nsheet.title = \"Students\"\nsheet[\"A1\"] = \"Name\"\nsheet[\"B1\"] = \"Score\"\nsheet.append([\"Alice\", 85])\nsheet.append([\"Bob\", 90])\nwb.save(\"scores.xlsx\")\n\n# Reading it back\nwb2 = load_workbook(\"scores.xlsx\")\nsheet2 = wb2.active\nfor name, score in sheet2.iter_rows(min_row=2, values_only=True):\n    print(name, score)"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 13: Working with Excel Spreadsheets", "url": "https://automatetheboringstuff.com/2e/chapter13/"}
                ]
            },
            {
                "title": "Working with CSV Files: csv.reader and csv.DictReader",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Reading Structured Text with the csv Module"},
                    {"type": "text", "value": "A CSV file is really just plain text with commas separating values -- you *could* parse it with `.split(\",\")`, but that breaks the moment a field itself contains a comma inside quotes. Python's built-in `csv` module handles those edge cases correctly, so it should always be used over manual splitting for real CSV data."},
                    {"type": "list", "ordered": False, "items": [
                        "`csv.reader(f)` -- yields each row as a plain list of strings",
                        "`csv.DictReader(f)` -- yields each row as a dict keyed by the header row's column names (much more readable code)",
                        "`csv.writer(f).writerow([...])` -- write a single row; `.writerows([...])` -- write many at once",
                        "always open CSV files with `newline=\"\"` on the `open()` call -- this is the documented, required pattern for the csv module to handle line endings correctly across platforms"
                    ]},
                    {"type": "callout", "kind": "info", "title": "DictReader Over reader for Readability", "value": "`row[\"amount\"]` is far clearer and more resilient to column reordering than `row[3]`. Reach for `csv.DictReader` by default, and drop down to plain `csv.reader` only when you specifically need positional access or the file has no header row."},
                    {"type": "code", "language": "python", "value": "import csv\n\nwith open(\"data.csv\", newline=\"\", encoding=\"utf-8\") as f:\n    reader = csv.DictReader(f)\n    for row in reader:\n        print(row[\"name\"], row[\"amount\"])\n\n# Writing a CSV\nwith open(\"out.csv\", \"w\", newline=\"\", encoding=\"utf-8\") as f:\n    writer = csv.writer(f)\n    writer.writerow([\"name\", \"amount\"])\n    writer.writerow([\"Alice\", 100.50])"},
                    {"type": "resource_link", "label": "\U0001F4C4 Python Docs -- csv Module", "url": "https://docs.python.org/3/library/csv.html"}
                ]
            },
            {
                "title": "Working with JSON Data: json.loads, json.dumps & APIs",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "JSON: The Language of APIs"},
                    {"type": "text", "value": "JSON (JavaScript Object Notation) is the standard format for data exchanged with web APIs. Python's built-in `json` module converts between JSON text and native Python objects: JSON objects become dicts, JSON arrays become lists, and the nesting maps directly."},
                    {"type": "list", "ordered": False, "items": [
                        "`json.loads(text)` -- parse a JSON *string* into Python objects",
                        "`json.load(file)` -- parse JSON directly from an open file object",
                        "`json.dumps(obj)` -- convert a Python object into a JSON string",
                        "`json.dumps(obj, indent=2)` -- pretty-printed, human-readable output",
                        "`response.json()` -- when using `requests`, this parses the response body as JSON in one call, equivalent to `json.loads(response.text)`"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "loads vs load -- Easy to Mix Up", "value": "`json.loads()` (with an 's') takes a **string**. `json.load()` (no 's') takes an already-open **file object**. Passing a string to `json.load()` or a file object to `json.loads()` raises a confusing error that doesn't obviously point back to this mistake."},
                    {"type": "code", "language": "python", "value": "import json\n\ndata = json.loads('{\"name\": \"Alice\", \"scores\": [85, 90, 78]}')\nprint(data[\"name\"])            # Alice\nprint(sum(data[\"scores\"]))     # 253\n\n# Convert Python back to a JSON string\noutput = json.dumps({\"status\": \"ok\", \"count\": 3})\nprint(output)   # {\"status\": \"ok\", \"count\": 3}"},
                    {"type": "resource_link", "label": "\U0001F4C4 Python Docs -- json Module", "url": "https://docs.python.org/3/library/json.html"}
                ]
            },
            {
                "title": "Converting Between Formats: CSV to JSON and Back",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Combining csv and json in One Pipeline"},
                    {"type": "text", "value": "A very common real-world script reads structured data in one format and re-emits it in another -- for example, exporting a database query as CSV for a spreadsheet, or converting a CSV export into JSON for an API. Since `csv.DictReader` already produces a list of dicts, feeding that straight into `json.dumps()` is often all that's needed."},
                    {"type": "list", "ordered": False, "items": [
                        "`list(csv.DictReader(f))` -- collect every row into a list of dicts in one line",
                        "`json.dumps(rows)` -- serialize that list directly to a JSON array of objects",
                        "Going the other way: `json.loads(text)` gives a list of dicts, and `csv.DictWriter(f, fieldnames=...)` writes them back out as CSV rows",
                        "Watch data types across the conversion -- CSV values are always strings; JSON preserves numbers and booleans as their real types, so a round trip through CSV can silently turn `90` into `\"90\"`"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Type Coercion Is the Main Gotcha Here", "value": "If a script reads numbers out of a CSV file, remember every field from `csv.reader`/`DictReader` is a plain string -- `\"90\" + \"10\"` concatenates to `\"9010\"`, it doesn't add to `100`. Explicitly cast with `int(...)` or `float(...)` before doing any arithmetic on CSV-sourced values."},
                    {"type": "code", "language": "python", "value": "import csv\nimport json\n\n# CSV -> JSON\nwith open(\"students.csv\", newline=\"\", encoding=\"utf-8\") as f:\n    rows = list(csv.DictReader(f))\n\nwith open(\"students.json\", \"w\", encoding=\"utf-8\") as f:\n    json.dump(rows, f, indent=2)\n\n# JSON -> CSV\nwith open(\"students.json\", encoding=\"utf-8\") as f:\n    data = json.load(f)\n\nwith open(\"students_out.csv\", \"w\", newline=\"\", encoding=\"utf-8\") as f:\n    writer = csv.DictWriter(f, fieldnames=data[0].keys())\n    writer.writeheader()\n    writer.writerows(data)"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 16: Working with CSV Files and JSON Data", "url": "https://automatetheboringstuff.com/2e/chapter16/"}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print(f"Inserted topic '{TOPIC_SLUG}' -> _id={result.inserted_id}")

    problems = [
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Sum a CSV Column",
            "difficulty": "easy",
            "description": "Simulate reading a CSV file. The first line of input is an integer N (number of data rows). The second line is the header row, comma-separated, and always includes a column named 'amount'. The next N lines are data rows. Print the sum of the 'amount' column, formatted to 2 decimal places.\n\nExample:\nInput:\n3\nname,amount\nalice,100.50\nbob,200.25\ncarol,50.00\nOutput: 350.75",
            "starter_code": "n = int(input())\nheader = input().split(\",\")\namount_idx = header.index(\"amount\")\ntotal = 0\nfor _ in range(n):\n    row = input().split(\",\")\n    total += float(row[amount_idx])\nprint(f\"{total:.2f}\")\n",
            "test_cases": [
                {"input": "3\nname,amount\nalice,100.50\nbob,200.25\ncarol,50.00", "expected_output": "350.75"},
                {"input": "2\nitem,amount\nx,10\ny,20", "expected_output": "30.00"},
                {"input": "1\nname,amount\nsolo,99.99", "expected_output": "99.99"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Convert CSV to JSON",
            "difficulty": "medium",
            "description": "Simulate converting a CSV file to JSON. First line: integer N (data rows). Second line: comma-separated header. Next N lines: data rows. Print a compact JSON array of objects (no extra spaces), one object per row, keyed by the header columns, values as strings.\n\nExample:\nInput:\n2\nname,age\nalice,30\nbob,25\nOutput: [{\"name\":\"alice\",\"age\":\"30\"},{\"name\":\"bob\",\"age\":\"25\"}]",
            "starter_code": "import json\n\nn = int(input())\nheader = input().split(\",\")\nrows = []\nfor _ in range(n):\n    values = input().split(\",\")\n    rows.append(dict(zip(header, values)))\n\nprint(json.dumps(rows, separators=(\",\", \":\")))\n",
            "test_cases": [
                {"input": "2\nname,age\nalice,30\nbob,25", "expected_output": "[{\"name\":\"alice\",\"age\":\"30\"},{\"name\":\"bob\",\"age\":\"25\"}]"},
                {"input": "1\nid,city\n1,delhi", "expected_output": "[{\"id\":\"1\",\"city\":\"delhi\"}]"},
                {"input": "3\nx,y\n1,2\n3,4\n5,6", "expected_output": "[{\"x\":\"1\",\"y\":\"2\"},{\"x\":\"3\",\"y\":\"4\"},{\"x\":\"5\",\"y\":\"6\"}]"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Average Score from JSON",
            "difficulty": "medium",
            "description": "Read a single line of JSON from stdin: an array of objects, each with a 'name' and a numeric 'score' field. Print the average of all the score values, formatted to 2 decimal places.\n\nExample:\nInput: [{\"name\": \"Alice\", \"score\": 85}, {\"name\": \"Bob\", \"score\": 90}, {\"name\": \"Carol\", \"score\": 78}]\nOutput: 84.33",
            "starter_code": "import json\n\ndata = json.loads(input())\nscores = [student[\"score\"] for student in data]\naverage = sum(scores) / len(scores)\nprint(f\"{average:.2f}\")\n",
            "test_cases": [
                {"input": "[{\"name\": \"Alice\", \"score\": 85}, {\"name\": \"Bob\", \"score\": 90}, {\"name\": \"Carol\", \"score\": 78}]", "expected_output": "84.33"},
                {"input": "[{\"name\": \"Solo\", \"score\": 100}]", "expected_output": "100.00"},
                {"input": "[{\"name\": \"A\", \"score\": 60}, {\"name\": \"B\", \"score\": 70}]", "expected_output": "65.00"}
            ]
        }
    ]

    result = await db.practice_problems.insert_many(problems)
    print(f"Inserted {len(result.inserted_ids)} practice problems for '{TOPIC_SLUG}'")

asyncio.run(main())
