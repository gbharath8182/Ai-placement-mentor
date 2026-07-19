import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "python",
    "slug": "python-functions",
    "title": "Functions & Scope",
    "difficulty": "beginner",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Defining Functions & Parameters",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Functions as Reusable Blocks"},
                {"type": "text", "value": "A function packages a block of code under a name so it can be called repeatedly without copy-pasting. Python functions are defined with `def`, can take **positional**, **keyword**, and **default** arguments, and can return any value (or `None` if no `return` statement runs)."},
                {"type": "list", "ordered": False, "items": [
                    "**Positional arguments** -- matched to parameters by order: `greet(\"Alice\", 30)`",
                    "**Keyword arguments** -- matched by name, order doesn't matter: `greet(age=30, name=\"Alice\")`",
                    "**Default arguments** -- `def greet(name, age=18):` -- `age` is optional",
                    "***args and **kwargs** -- `*args` collects extra positional args into a tuple, `**kwargs` collects extra keyword args into a dict"
                ]},
                {"type": "callout", "kind": "warning", "title": "The mutable default argument trap", "value": "`def add_item(item, lst=[]):` looks harmless but the default list is created **once**, at function definition time, and shared across every call that doesn't pass its own list -- leading to bizarre bugs where old calls' data leaks into new ones. Always use `lst=None` and create the list inside the function body instead."},
                {"type": "code", "language": "python", "value": "def greet(name, age=18, *args, **kwargs):\n    print(f\"Hello {name}, age {age}\")\n    print(\"Extra positional:\", args)\n    print(\"Extra keyword:\", kwargs)\n\ngreet(\"Alice\", 30, \"extra1\", \"extra2\", city=\"NYC\", job=\"Engineer\")\n\n# The mutable default argument bug, and its fix\ndef add_item_buggy(item, lst=[]):\n    lst.append(item)\n    return lst\n\ndef add_item_fixed(item, lst=None):\n    if lst is None:\n        lst = []\n    lst.append(item)\n    return lst"},
                {"type": "resource_link", "label": "\U0001F4D6 Automate the Boring Stuff: Ch. 3, Functions", "url": "https://automatetheboringstuff.com/2e/chapter3/"}
            ]
        },
        {
            "title": "Scope & the LEGB Rule",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Where Python Looks for a Name"},
                {"type": "text", "value": "When Python encounters a variable name, it searches four scopes in order -- **L**ocal, **E**nclosing, **G**lobal, **B**uilt-in -- and uses the first match it finds. This is why a variable defined inside a function doesn't leak out, but a function can still read (not modify) variables from the enclosing/global scope."},
                {"type": "list", "ordered": False, "items": [
                    "**Local** -- variables assigned inside the current function",
                    "**Enclosing** -- variables in any outer function (relevant for nested/closure functions)",
                    "**Global** -- variables assigned at module level",
                    "**Built-in** -- Python's own names like `len`, `print`, `range`"
                ]},
                {"type": "callout", "kind": "important", "title": "global and nonlocal keywords", "value": "Reading an outer-scope variable works automatically, but **assigning** to one from inside a function requires an explicit `global` (for module-level) or `nonlocal` (for an enclosing function) declaration -- otherwise Python creates a brand-new local variable instead of modifying the outer one, a very common source of confusion."},
                {"type": "code", "language": "python", "value": "counter = 0\n\ndef increment_broken():\n    counter += 1  # UnboundLocalError -- Python sees the assignment and treats counter as local\n\ndef increment_fixed():\n    global counter\n    counter += 1\n\n# Closures use the Enclosing scope\ndef make_multiplier(factor):\n    def multiplier(x):\n        return x * factor  # 'factor' is read from the enclosing scope\n    return multiplier\n\ntriple = make_multiplier(3)\nprint(triple(7))  # 21"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Python Scope of Variables", "url": "https://www.geeksforgeeks.org/python-scope-of-variables/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "python-functions",
        "title": "Sum with Default Argument",
        "difficulty": "easy",
        "description": "Write a function add(a, b=10) that returns a + b. Given two space-separated integers on one line (if only one integer is given, use the default for b), print the result.",
        "starter_code": "def add(a, b=10):\n    return a + b\n\nimport sys\nparts = sys.stdin.readline().split()\nif len(parts) == 2:\n    print(add(int(parts[0]), int(parts[1])))\nelse:\n    print(add(int(parts[0])))",
        "test_cases": [
            {"input": "5 3", "expected_output": "8"},
            {"input": "7", "expected_output": "17"},
            {"input": "0 0", "expected_output": "0"}
        ]
    },
    {
        "topic_slug": "python-functions",
        "title": "Closure Counter",
        "difficulty": "medium",
        "description": "Implement make_counter() which returns a function that, each time it's called, returns the next integer starting from 1 (using a closure, not a global variable). Given an integer n, call the returned function n times and print the final value.",
        "starter_code": "def make_counter():\n    count = 0\n    def counter():\n        nonlocal count\n        count += 1\n        return count\n    return counter\n\nimport sys\nn = int(sys.stdin.readline())\nc = make_counter()\nresult = None\nfor _ in range(n):\n    result = c()\nprint(result)",
        "test_cases": [
            {"input": "3", "expected_output": "3"},
            {"input": "1", "expected_output": "1"},
            {"input": "10", "expected_output": "10"}
        ]
    }
]

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    existing = await db.topics.find_one({"slug": TOPIC["slug"]})
    if existing:
        print("SKIP -- topic already exists:", TOPIC["slug"])
    else:
        await db.topics.insert_one(TOPIC)
        print("Inserted topic:", TOPIC["slug"])

    for problem in PRACTICE_PROBLEMS:
        existing_p = await db.practice_problems.find_one({"topic_slug": problem["topic_slug"], "title": problem["title"]})
        if existing_p:
            print("SKIP -- problem already exists:", problem["title"])
        else:
            await db.practice_problems.insert_one(problem)
            print("Inserted problem:", problem["title"])

asyncio.run(main())
