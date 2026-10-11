import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC_SLUG = "python-files"

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    await db.topics.delete_many({"slug": TOPIC_SLUG})
    await db.practice_problems.delete_many({"topic_slug": TOPIC_SLUG})

    topic = {
        "domain_slug": "python",
        "slug": TOPIC_SLUG,
        "title": "Reading & Writing Files",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "File Paths with pathlib: Modern, Cross-Platform Path Handling",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Why pathlib Over Raw String Paths"},
                    {"type": "text", "value": "Older Python code builds file paths with plain string concatenation, like `\"data\" + \"/\" + \"file.txt\"`. This breaks on Windows, where the separator is `\\` instead of `/`. The `pathlib` module fixes this by representing a path as a `Path` object -- an object that knows how to join, inspect, and manipulate itself correctly on whatever operating system it's running on."},
                    {"type": "text", "value": "The `/` operator is overloaded on `Path` objects specifically to join path segments, which reads naturally once you're used to it: `Path(\"data\") / \"reports\" / \"summary.txt\"`."},
                    {"type": "list", "ordered": False, "items": [
                        "`Path(\"a\") / \"b\" / \"c.txt\"` -- joins segments, correct separator on any OS",
                        "`p.exists()` -- True if the path exists on disk",
                        "`p.is_file()` / `p.is_dir()` -- check what kind of thing it is",
                        "`p.name` -- final component, e.g. `\"summary.txt\"`",
                        "`p.suffix` -- extension, e.g. `\".txt\"`; `p.stem` -- name without extension, e.g. `\"summary\"`",
                        "`p.parent` -- the containing directory as another `Path`"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Never Hardcode a Path Separator", "value": "Writing `\"data\\\\\" + filename` or `\"data/\" + filename` will work on one OS and silently break on the other. Always build paths with `Path(...) / ...` (or `os.path.join`) so the correct separator is chosen automatically at runtime."},
                    {"type": "code", "language": "python", "value": "from pathlib import Path\n\np = Path(\"reports\") / \"2026\" / \"summary.txt\"\nprint(p)         # reports/2026/summary.txt (or reports\\2026\\summary.txt on Windows)\nprint(p.name)     # summary.txt\nprint(p.suffix)   # .txt\nprint(p.stem)     # summary\nprint(p.parent)   # reports/2026"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 8: Reading and Writing Files", "url": "https://automatetheboringstuff.com/2e/chapter8/"}
                ]
            },
            {
                "title": "Reading Files: open(), Context Managers & Iteration",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "The with Statement: Why It's Non-Negotiable"},
                    {"type": "text", "value": "`open(path, mode)` returns a file object connected to a file on disk. The critical habit is to always open files using a `with` block: `with open(path) as f:`. This guarantees the file is properly closed when the block ends -- **even if an exception is raised inside it** -- whereas manually calling `f.close()` after your code can easily be skipped if something throws first."},
                    {"type": "list", "ordered": False, "items": [
                        "`f.read()` -- entire file contents as one string (careful with huge files)",
                        "`f.readline()` -- one line at a time, including the trailing newline",
                        "`f.readlines()` -- entire file as a list of line-strings",
                        "`for line in f:` -- iterate line by line without loading the whole file into memory at once (best for large files)",
                        "mode `\"r\"` (read, default), `\"w\"` (write/overwrite), `\"a\"` (append), `\"r+\"` (read and write)"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "Forgetting to Close a File Has Real Consequences", "value": "Leaving files open leaks file handles (your OS has a limit) and, for files opened for writing, can mean buffered data never actually gets flushed to disk if the program crashes first. The `with` statement removes this risk entirely -- there is essentially never a good reason to call `open()` outside of one."},
                    {"type": "code", "language": "python", "value": "# Read line by line, memory-efficient for large files\nwith open(\"notes.txt\") as f:\n    for line in f:\n        print(line.strip())   # .strip() removes the trailing '\\n'\n\n# Read the whole file at once\nwith open(\"notes.txt\") as f:\n    contents = f.read()\nprint(len(contents))"},
                    {"type": "resource_link", "label": "\U0001F4C4 Python Docs -- Reading and Writing Files", "url": "https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files"}
                ]
            },
            {
                "title": "Writing & Appending to Files",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Write Mode vs Append Mode"},
                    {"type": "text", "value": "Opening a file with mode `\"w\"` truncates it -- the moment `open()` succeeds, the existing file content is gone, whether or not you ever call `.write()`. Mode `\"a\"` instead appends to the end of the file, leaving existing content untouched. Confusing the two is one of the most common ways beginners accidentally destroy real data."},
                    {"type": "list", "ordered": False, "items": [
                        "`f.write(text)` -- writes a string; unlike `print()`, it does **not** add a newline automatically -- you must include `\\n` yourself",
                        "`f.writelines(list_of_strings)` -- writes each string in the list, again with no automatic newlines added",
                        "`\"w\"` -- create new / **overwrite and erase** existing content",
                        "`\"a\"` -- create new / append to existing content, nothing is erased",
                        "`open(path, \"w\", encoding=\"utf-8\")` -- always specify `encoding=\"utf-8\"` explicitly when writing text that might contain non-ASCII characters"
                    ]},
                    {"type": "callout", "kind": "important", "title": "'w' Mode Destroys Data Immediately, Not Just on Write", "value": "`with open(\"important_data.txt\", \"w\") as f:` erases the file's previous contents the instant it runs -- even if the code inside the block never calls `.write()` at all, or crashes on the next line. Before writing any script that opens a real file in `\"w\"` mode, double-check you actually meant to overwrite it, not append (`\"a\"`) to it."},
                    {"type": "code", "language": "python", "value": "lines = [\"Report generated\", \"Status: OK\", \"Items processed: 42\"]\n\n# Write mode: creates the file fresh, erasing any prior content\nwith open(\"report.txt\", \"w\", encoding=\"utf-8\") as f:\n    for line in lines:\n        f.write(line + \"\\n\")   # must add '\\n' manually\n\n# Append mode: adds to the end without touching what's already there\nwith open(\"report.txt\", \"a\", encoding=\"utf-8\") as f:\n    f.write(\"-- end of report --\\n\")"},
                    {"type": "resource_link", "label": "\U0001F4C4 Python Docs -- open() Built-in Function Reference", "url": "https://docs.python.org/3/library/functions.html#open"}
                ]
            },
            {
                "title": "Organizing Files: shutil, os.walk & Pattern Matching",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Automating File Organization"},
                    {"type": "text", "value": "Beyond reading and writing a single file, real automation scripts often need to copy, move, and search across entire directory trees. The `shutil` module handles copying and moving; `os.walk()` recursively visits every file and folder under a starting directory; and `glob` lets you find files by wildcard pattern instead of listing everything manually."},
                    {"type": "list", "ordered": False, "items": [
                        "`shutil.copy(src, dst)` -- copy a single file",
                        "`shutil.move(src, dst)` -- move (or rename) a file or folder",
                        "`shutil.copytree(src, dst)` -- recursively copy an entire directory tree",
                        "`os.walk(root)` -- yields `(dirpath, dirnames, filenames)` for every directory under `root`, top-down",
                        "`glob.glob(\"*.txt\")` -- returns all filenames in the current directory matching the wildcard pattern"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "shutil.rmtree() Has No Undo", "value": "`shutil.rmtree(path)` recursively deletes an entire directory tree immediately and permanently -- there is no recycle bin, no confirmation prompt, and no built-in way to recover it. Before calling it in any script, especially one where the path is built from user input or a variable rather than a hardcoded literal, print the path first and sanity-check it."},
                    {"type": "code", "language": "python", "value": "import os\n\n# Recursively count files by extension under a directory tree\ncounts = {}\nfor dirpath, dirnames, filenames in os.walk(\"project\"):\n    for name in filenames:\n        ext = name.rsplit(\".\", 1)[-1] if \".\" in name else \"noext\"\n        counts[ext] = counts.get(ext, 0) + 1\n\nfor ext, count in sorted(counts.items()):\n    print(f\"{ext}: {count}\")"},
                    {"type": "resource_link", "label": "\U0001F4C4 Automate the Boring Stuff -- Chapter 9: Organizing Files", "url": "https://automatetheboringstuff.com/2e/chapter9/"},
                    {"type": "resource_link", "label": "\U0001F4C4 Python Docs -- shutil: High-Level File Operations", "url": "https://docs.python.org/3/library/shutil.html"}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print(f"Inserted topic '{TOPIC_SLUG}' -> _id={result.inserted_id}")

    problems = [
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Count Non-Empty Lines",
            "difficulty": "easy",
            "description": "Simulate scanning a file's contents. The first line of input is an integer N, the number of lines that follow. Read N lines and print how many of them contain at least one non-whitespace character (i.e. are not blank or whitespace-only).\n\nExample:\nInput:\n5\nhello\n   \nworld\n\nfoo bar\nOutput: 3",
            "starter_code": "n = int(input())\ncount = 0\nfor _ in range(n):\n    line = input()\n    if line.strip():\n        count += 1\nprint(count)\n",
            "test_cases": [
                {"input": "5\nhello\n   \nworld\n\nfoo bar", "expected_output": "3"},
                {"input": "3\na\nb\nc", "expected_output": "3"},
                {"input": "2\n\n   ", "expected_output": "0"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Most Frequent Word Across Lines",
            "difficulty": "medium",
            "description": "Simulate reading N lines of text (first input line is the integer N). Combine the words from all lines and print the single most frequently occurring word. If there is a tie, print whichever tied word appeared first in the input.\n\nExample:\nInput:\n3\nthe quick brown\nfox jumps the\nthe fox runs\nOutput: the",
            "starter_code": "from collections import Counter\n\nn = int(input())\nwords = []\nfor _ in range(n):\n    line = input()\n    words.extend(line.split())\n\ncounts = Counter(words)\nmost_common_word, _ = counts.most_common(1)[0]\nprint(most_common_word)\n",
            "test_cases": [
                {"input": "3\nthe quick brown\nfox jumps the\nthe fox runs", "expected_output": "the"},
                {"input": "2\napple banana apple\nbanana apple banana", "expected_output": "apple"},
                {"input": "1\nsingle", "expected_output": "single"}
            ]
        },
        {
            "topic_slug": TOPIC_SLUG,
            "title": "Count Files by Extension",
            "difficulty": "medium",
            "description": "Simulate organizing a directory listing. The first line of input is an integer N, followed by N filenames (one per line, some may have no extension). Print each distinct extension and its count, one per line, in the format ext:count, sorted alphabetically by extension. Files with no '.' should be grouped under 'noext'.\n\nExample:\nInput:\n5\nreport.txt\nscript.py\nnotes.txt\nmain.py\nREADME\nOutput:\nnoext:1\npy:2\ntxt:2",
            "starter_code": "n = int(input())\ncounts = {}\nfor _ in range(n):\n    filename = input().strip()\n    if \".\" in filename:\n        ext = filename.rsplit(\".\", 1)[1]\n    else:\n        ext = \"noext\"\n    counts[ext] = counts.get(ext, 0) + 1\n\nfor ext in sorted(counts):\n    print(f\"{ext}:{counts[ext]}\")\n",
            "test_cases": [
                {"input": "5\nreport.txt\nscript.py\nnotes.txt\nmain.py\nREADME", "expected_output": "noext:1\npy:2\ntxt:2"},
                {"input": "3\na.jpg\nb.jpg\nc.png", "expected_output": "jpg:2\npng:1"},
                {"input": "1\nsingle.py", "expected_output": "py:1"}
            ]
        }
    ]

    result = await db.practice_problems.insert_many(problems)
    print(f"Inserted {len(result.inserted_ids)} practice problems for '{TOPIC_SLUG}'")

asyncio.run(main())
