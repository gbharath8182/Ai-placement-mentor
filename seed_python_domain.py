from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/education_platform")
db = client.education_platform

doc = {
    "domain_slug": "python",
    "overview": "Python Programming covers the general-purpose, high-level language that has become the default first language for most learners and one of the most in-demand languages in industry -- used across web backends, data science, automation/scripting, AI/ML, and DevOps tooling. This domain focuses on core language fluency: syntax, data structures, object-oriented design, and the standard library patterns that show up daily in real codebases.",
    "why_important": "Python is consistently ranked among the top 2-3 most in-demand languages on job boards worldwide, and is the default language for machine learning, data engineering, automation, and a large share of backend web development (Django, FastAPI, Flask). Its readability makes it the most common language for technical screens even at companies that don't use it in production, because it lets interviewers focus on problem-solving logic rather than syntax friction.",
    "industries_using": [
        "AI/ML and Data Science",
        "Web backend development (Django, FastAPI, Flask)",
        "Automation, scripting, and DevOps tooling",
        "Fintech and quantitative analysis",
        "Scientific computing and research",
        "Cybersecurity and penetration testing tooling"
    ],
    "future_scope": "Python's dominance in AI/ML ensures continued demand as more companies build AI-adjacent products. Its role as the 'glue language' for automation, data pipelines, and infrastructure-as-code (Ansible, and much of the Python-based tooling behind cloud platforms) means Python fluency compounds in value with specializations like data engineering, ML engineering, or backend development, rather than being a narrow, isolated skill.",
    "average_salary": "Rs 4-10 LPA entry-level (India, general backend/automation roles), Rs 8-20+ LPA for Python roles specializing in data/ML -- 70k-160k USD+ entry-level in the US depending on specialization",
    "skills_required": [
        "Core Python syntax and data types",
        "Object-oriented programming in Python",
        "Standard library familiarity (collections, itertools, os, json, datetime)",
        "Virtual environments and package management (pip, venv)",
        "Debugging and reading tracebacks",
        "Writing and reading unit tests (pytest/unittest)",
        "Basic familiarity with at least one framework (Django/Flask/FastAPI) or data library (pandas/NumPy) depending on specialization"
    ],
    "prerequisites": [
        "Basic computer literacy",
        "Comfort installing software and using a command line",
        "No prior programming experience strictly required, though helpful"
    ],
    "roadmap": [
        {
            "tier": "beginner",
            "items": [
                "Variables, data types, and operators",
                "Control flow: if/elif/else, for and while loops",
                "Functions: parameters, return values, default arguments, *args/**kwargs",
                "Core data structures: lists, tuples, dictionaries, sets",
                "String manipulation and formatting (f-strings)",
                "Basic file reading/writing"
            ]
        },
        {
            "tier": "intermediate",
            "items": [
                "Object-oriented programming: classes, inheritance, dunder methods",
                "Exception handling: try/except/finally, custom exceptions",
                "List/dict/set comprehensions and generator expressions",
                "Modules, packages, and virtual environments (venv, pip)",
                "Working with JSON, CSV, and basic API requests (requests library)",
                "Unit testing with pytest or unittest"
            ]
        },
        {
            "tier": "advanced",
            "items": [
                "Iterators, generators, and the iterator protocol",
                "Decorators and context managers",
                "Multithreading, multiprocessing, and asyncio basics",
                "Type hints and static type checking (mypy)",
                "Packaging a project for distribution (pyproject.toml)",
                "Performance profiling (cProfile) and basic optimization"
            ]
        }
    ],
    "topics": [
        {
            "name": "Python Syntax & Data Types",
            "description": "The foundational building blocks of Python: variables, dynamic typing, numeric/string/boolean types, and Python's core operators.",
            "importance": "Everything else in the language builds on this; interviewers use trivial-looking syntax questions to catch candidates who learned Python superficially.",
            "difficulty": "beginner",
            "estimated_time": "1 week",
            "prerequisites": [],
            "resources": {
                "documentation": "https://docs.python.org/3/tutorial/introduction.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9agICnT8t4iYVSZ3eykIAOME",
                "articles": [
                    "https://www.geeksforgeeks.org/python-data-types/"
                ],
                "notes": "Understand Python's dynamic typing model (variables are labels, not typed boxes) early -- it explains a lot of otherwise-confusing behavior later.",
                "practice_platform": "HackerRank Python (Basic) track",
                "cheat_sheet": "int/float/str/bool/None are immutable; mutable vs immutable matters for default arguments and function behavior"
            },
            "practice_questions": [
                "What is the difference between a list and a tuple?",
                "Why can't you use a list as a dictionary key?",
                "Explain Python's dynamic typing vs static typing",
                "What does is vs == check for?",
                "What is the difference between / and // division?"
            ],
            "projects": [
                "Build a command-line unit converter (temperature, currency, length)"
            ],
            "interview_questions": [
                "What are Python's built-in immutable types?",
                "Explain mutable default argument pitfalls with an example",
                "What is the difference between a shallow copy and a deep copy?",
                "How does Python's garbage collection work at a high level?"
            ]
        },
        {
            "name": "Control Flow & Functions",
            "description": "Conditional logic, loops, and function definitions including default arguments, keyword arguments, and variable-length argument lists.",
            "importance": "Functions are the primary unit of reuse in Python; misunderstanding argument passing (especially *args/**kwargs and mutable defaults) is one of the most common source of real bugs.",
            "difficulty": "beginner",
            "estimated_time": "1 week",
            "prerequisites": ["Python Syntax & Data Types"],
            "resources": {
                "documentation": "https://docs.python.org/3/tutorial/controlflow.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9agwh1XjRt242xIpHhPT2llg",
                "articles": [
                    "https://www.geeksforgeeks.org/python-functions/"
                ],
                "notes": "Practice writing functions with *args and **kwargs until unpacking feels automatic -- it shows up constantly in real code and interviews.",
                "practice_platform": "LeetCode Python-specific 'Easy' problems",
                "cheat_sheet": "*args -> tuple of positional args, **kwargs -> dict of keyword args; default args are evaluated once at def time"
            },
            "practice_questions": [
                "Write a function that accepts any number of positional and keyword arguments and prints them",
                "Explain why using a mutable default argument like def f(x=[]) is dangerous",
                "Write a recursive function to compute factorial",
                "What is the difference between a positional-only and keyword-only argument?",
                "Implement a simple FizzBuzz"
            ],
            "projects": [
                "Build a simple calculator CLI supporting +, -, *, / with input validation"
            ],
            "interview_questions": [
                "What is a closure in Python and how would you use one?",
                "Explain the LEGB rule for variable scope resolution",
                "What does the global and nonlocal keyword do?",
                "How would you memoize a function without using a library?"
            ]
        },
        {
            "name": "Core Data Structures (Lists, Dicts, Sets, Tuples)",
            "description": "Python's built-in collection types, their performance characteristics, and idiomatic usage patterns including comprehensions.",
            "importance": "The most frequently used feature of Python day-to-day; comprehension syntax and dictionary usage patterns are a very common interview and take-home theme.",
            "difficulty": "beginner",
            "estimated_time": "1-1.5 weeks",
            "prerequisites": ["Python Syntax & Data Types"],
            "resources": {
                "documentation": "https://docs.python.org/3/tutorial/datastructures.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9ah7DDtYtflgwMwpT3xmjXY0",
                "articles": [
                    "https://www.geeksforgeeks.org/python-list-vs-dictionary/"
                ],
                "notes": "Know Big-O for common operations on each structure (append vs insert(0), dict lookup vs list search) -- this comes up constantly.",
                "practice_platform": "LeetCode (filter by Python solutions)",
                "cheat_sheet": "list: O(1) append, O(n) insert/search; dict/set: O(1) average lookup; tuple: immutable, hashable if contents are hashable"
            },
            "practice_questions": [
                "Write a dictionary comprehension to invert a dict's keys and values",
                "Remove duplicates from a list while preserving order",
                "Find the intersection of two lists using sets",
                "Explain why dict keys must be hashable",
                "Sort a list of dictionaries by a specific key"
            ],
            "projects": [
                "Build a word-frequency counter that reads a text file and prints the top 10 most common words"
            ],
            "interview_questions": [
                "What's the time complexity of dictionary lookup, and why?",
                "When would you use a set over a list?",
                "What is a namedtuple and when would you use one over a dict?",
                "Explain list slicing and how negative indices work"
            ]
        },
        {
            "name": "Object-Oriented Programming in Python",
            "description": "Classes, inheritance, magic/dunder methods, and Python-specific OOP idioms like properties and class/static methods.",
            "importance": "Nearly every non-trivial Python codebase uses classes; dunder methods and property usage are a strong signal of real Python fluency versus surface-level scripting knowledge.",
            "difficulty": "intermediate",
            "estimated_time": "1.5-2 weeks",
            "prerequisites": ["Control Flow & Functions", "Core Data Structures (Lists, Dicts, Sets, Tuples)"],
            "resources": {
                "documentation": "https://docs.python.org/3/tutorial/classes.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9agS67Uits0UnJyrYiXhDS6q",
                "articles": [
                    "https://www.geeksforgeeks.org/python-oops-concepts/"
                ],
                "notes": "Implement __repr__, __eq__, and __len__ on a custom class at least once -- these dunder methods are what makes Python classes feel 'native'.",
                "practice_platform": "GeeksforGeeks Python OOP practice section",
                "cheat_sheet": "__init__ = constructor, __repr__ = debug string, __str__ = readable string, @staticmethod = no self/cls, @classmethod = receives cls"
            },
            "practice_questions": [
                "Implement a class with __eq__ and __hash__ so instances can be used in a set",
                "What is the difference between @staticmethod and @classmethod?",
                "Implement a simple BankAccount class with deposit/withdraw and balance validation",
                "Explain Python's method resolution order (MRO) with multiple inheritance",
                "What does the super() function do?"
            ],
            "projects": [
                "Build a small inventory management system using classes for Product, Inventory, and Transaction"
            ],
            "interview_questions": [
                "Explain the difference between __new__ and __init__",
                "What is duck typing and how does it relate to Python's OOP model?",
                "How do you make a class immutable in Python?",
                "What is a metaclass, at a high level?"
            ]
        },
        {
            "name": "File Handling & Exception Handling",
            "description": "Reading and writing files safely, working with context managers, and structuring robust error handling with try/except/finally and custom exceptions.",
            "importance": "Real-world scripts and services constantly deal with I/O and failure modes; interviewers use this topic to check whether a candidate writes production-safe code or only 'happy path' code.",
            "difficulty": "intermediate",
            "estimated_time": "1 week",
            "prerequisites": ["Control Flow & Functions"],
            "resources": {
                "documentation": "https://docs.python.org/3/tutorial/errors.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9agAiWp6Y41ueUKx7T7ObNSO",
                "articles": [
                    "https://www.geeksforgeeks.org/python-exception-handling/"
                ],
                "notes": "Always prefer 'with open(...) as f' over manual open/close -- it's both idiomatic and safer against leaked file handles.",
                "practice_platform": "HackerRank Python (Exceptions) track",
                "cheat_sheet": "with = context manager, guarantees cleanup; except SpecificError beats bare except; finally always runs"
            },
            "practice_questions": [
                "Write a function that safely reads a file and returns None if it doesn't exist",
                "Create a custom exception class and raise it with a meaningful message",
                "What is the difference between except Exception and a bare except:?",
                "Explain what happens if an exception is raised inside a finally block",
                "Write a context manager using the @contextmanager decorator"
            ],
            "projects": [
                "Build a log-file parser that safely handles missing files, malformed lines, and encoding errors"
            ],
            "interview_questions": [
                "Why is using a bare except: considered bad practice?",
                "How would you implement your own context manager class using __enter__/__exit__?",
                "What's the difference between raise and raise from?",
                "How do you re-raise an exception after logging it?"
            ]
        },
        {
            "name": "Iterators, Generators & Decorators",
            "description": "The iterator protocol, lazy evaluation with generators, and function-wrapping via decorators -- the features most associated with idiomatic, 'Pythonic' code.",
            "importance": "A strong differentiator between beginner and intermediate Python developers; generators for memory-efficient data processing and decorators for cross-cutting concerns (logging, timing, auth) appear constantly in real codebases and interviews.",
            "difficulty": "advanced",
            "estimated_time": "1.5-2 weeks",
            "prerequisites": ["Object-Oriented Programming in Python"],
            "resources": {
                "documentation": "https://docs.python.org/3/howto/functional.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9ah08qLM9m2GsQg4t9uw5hFY",
                "articles": [
                    "https://www.geeksforgeeks.org/generators-in-python/"
                ],
                "notes": "Write a generator using yield and a decorator using functools.wraps at least once each -- reading about them isn't a substitute for tracing through the execution order yourself.",
                "practice_platform": "LeetCode + write-your-own practice on GitHub",
                "cheat_sheet": "yield pauses/resumes function state; generators are lazy (memory-efficient); decorators = functions that wrap other functions"
            },
            "practice_questions": [
                "Write a generator function that yields Fibonacci numbers infinitely",
                "Implement a timing decorator that prints how long a function took to run",
                "What is the difference between a generator and a list comprehension in terms of memory?",
                "Explain what functools.wraps does and why it matters",
                "Write a decorator that caches function results (a simple memoizer)"
            ],
            "projects": [
                "Build a lazy CSV-row processor using a generator that can handle files larger than memory"
            ],
            "interview_questions": [
                "How does the iterator protocol (__iter__/__next__) work under the hood?",
                "What's the difference between yield and return?",
                "How would you write a decorator that accepts arguments (e.g. @retry(times=3))?",
                "What is a generator expression and how does it differ from a list comprehension syntactically and in behavior?"
            ]
        },
        {
            "name": "Modules, Packages & Virtual Environments",
            "description": "Organizing code into modules and packages, managing dependencies with pip, and isolating project environments with venv.",
            "importance": "Every real Python project depends on this; dependency conflicts and environment mismanagement are among the most common early-career debugging headaches.",
            "difficulty": "beginner",
            "estimated_time": "3-5 days",
            "prerequisites": [],
            "resources": {
                "documentation": "https://docs.python.org/3/tutorial/venv.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9aiXlHcLx-mDH1Qul38wD3aR",
                "articles": [
                    "https://www.geeksforgeeks.org/python-virtual-environment/"
                ],
                "notes": "Get comfortable creating a venv, activating it, and generating/using a requirements.txt from scratch without copy-pasting commands.",
                "practice_platform": "Practice on any small personal project",
                "cheat_sheet": "python -m venv env -> create, source env/bin/activate -> activate (Linux/Mac), env\\Scripts\\activate -> activate (Windows), pip freeze > requirements.txt"
            },
            "practice_questions": [
                "What is the difference between a module and a package in Python?",
                "Why should you always use a virtual environment per project?",
                "What does __init__.py do in a package?",
                "How does Python resolve import statements (sys.path)?",
                "What's the difference between pip install and pip install -e ."
            ],
            "projects": [
                "Package a small utility script as an installable local package with a pyproject.toml"
            ],
            "interview_questions": [
                "How would you resolve a dependency version conflict between two packages?",
                "What is the difference between requirements.txt and pyproject.toml?",
                "Explain what happens during 'pip install' at a high level",
                "What is a namespace package?"
            ]
        },
        {
            "name": "Concurrency: Threading, Multiprocessing & Asyncio",
            "description": "Python's approaches to concurrent and parallel execution -- threading (I/O-bound), multiprocessing (CPU-bound), and asyncio (cooperative single-threaded concurrency) -- and the Global Interpreter Lock (GIL) that shapes all three.",
            "importance": "A frequent advanced interview topic and directly relevant to real performance work; misunderstanding the GIL leads to real production bugs like assuming threading speeds up CPU-bound code.",
            "difficulty": "advanced",
            "estimated_time": "2 weeks",
            "prerequisites": ["Iterators, Generators & Decorators"],
            "resources": {
                "documentation": "https://docs.python.org/3/library/asyncio.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLu0W_9lII9ajQKr_bWl1cVA3D3H8fSC1U",
                "articles": [
                    "https://www.geeksforgeeks.org/multithreading-python-set-1/"
                ],
                "notes": "Know exactly when to reach for each: threading for I/O-bound waiting, multiprocessing for CPU-bound crunching, asyncio for high-volume I/O-bound concurrency without thread overhead.",
                "practice_platform": "Build small scripts and time them under each approach",
                "cheat_sheet": "GIL = only one thread executes Python bytecode at a time; threading helps I/O-bound, multiprocessing helps CPU-bound, asyncio helps I/O-bound at scale"
            },
            "practice_questions": [
                "Explain the GIL and why it limits threading for CPU-bound work",
                "When would you choose multiprocessing over threading?",
                "Write a simple async function using async/await that fetches two URLs concurrently",
                "What is a race condition and how do you prevent one using a Lock?",
                "What is the difference between concurrency and parallelism?"
            ],
            "projects": [
                "Build a concurrent web scraper using asyncio and aiohttp that fetches multiple pages in parallel"
            ],
            "interview_questions": [
                "Why doesn't threading speed up a CPU-bound Python function?",
                "How does asyncio achieve concurrency without multiple threads?",
                "What is a deadlock and how could it occur in Python threading code?",
                "How would you share state safely between multiple processes?"
            ]
        }
    ],
    "skills": [
        {
            "name": "Core Python Fluency",
            "description": "Writing idiomatic, correct Python covering syntax, data structures, and control flow without friction.",
            "importance": "The baseline requirement for every Python role and technical screen.",
            "level": "beginner",
            "estimated_hours": 20
        },
        {
            "name": "Object-Oriented Design in Python",
            "description": "Structuring code with classes, inheritance, and Python-specific idioms like dunder methods and properties.",
            "importance": "Required for any codebase beyond simple scripts.",
            "level": "intermediate",
            "estimated_hours": 20
        },
        {
            "name": "Generators & Decorators",
            "description": "Writing memory-efficient, reusable code using Python's functional and lazy-evaluation features.",
            "importance": "A strong signal of intermediate-to-advanced Python fluency, frequently tested in interviews.",
            "level": "advanced",
            "estimated_hours": 15
        },
        {
            "name": "Concurrency Fundamentals",
            "description": "Choosing and implementing the right concurrency model (threading/multiprocessing/asyncio) for a given problem.",
            "importance": "Directly impacts real-world performance and is a common advanced interview topic.",
            "level": "advanced",
            "estimated_hours": 25
        },
        {
            "name": "Dependency & Environment Management",
            "description": "Managing virtual environments, dependencies, and packaging for real projects.",
            "importance": "A daily practical skill; gaps here cause real friction in team environments.",
            "level": "beginner",
            "estimated_hours": 8
        }
    ],
    "practice_platforms": [
        "LeetCode",
        "HackerRank",
        "GeeksforGeeks",
        "Codewars",
        "Exercism (Python track)"
    ],
    "projects": [
        {
            "title": "CLI Task Manager",
            "description": "A command-line to-do list application with add/list/complete/delete commands, persisting data to a local JSON file.",
            "skills_learned": ["File I/O", "JSON handling", "CLI argument parsing"],
            "technologies_used": ["Python", "argparse or click", "json"],
            "github_ideas": ["python-cli-task-manager"],
            "tier": "beginner"
        },
        {
            "title": "Custom Data Structure Library",
            "description": "Implement a custom LinkedList, Stack, and Queue as proper Python classes with dunder methods for iteration and representation.",
            "skills_learned": ["OOP", "Dunder methods", "Iterator protocol"],
            "technologies_used": ["Python"],
            "github_ideas": ["python-ds-from-scratch"],
            "tier": "intermediate"
        },
        {
            "title": "Async Web Scraper & Aggregator",
            "description": "A concurrent scraper that fetches data from multiple sources using asyncio/aiohttp, aggregates results, and writes them to a CSV.",
            "skills_learned": ["Asyncio", "Concurrent I/O", "Data aggregation"],
            "technologies_used": ["Python", "asyncio", "aiohttp"],
            "github_ideas": ["async-scraper-aggregator"],
            "tier": "advanced"
        },
        {
            "title": "Mini Web Framework Clone",
            "description": "A stripped-down WSGI-based web framework supporting basic routing and request handling, to understand how frameworks like Flask work internally.",
            "skills_learned": ["Decorators", "Closures", "HTTP fundamentals"],
            "technologies_used": ["Python", "wsgiref"],
            "github_ideas": ["mini-web-framework"],
            "tier": "advanced"
        }
    ],
    "interview_prep": {
        "important_topics": [
            "Core data structures and their complexity",
            "OOP and dunder methods",
            "Generators and decorators",
            "Exception handling patterns",
            "Concurrency (GIL, threading vs multiprocessing vs asyncio)"
        ],
        "frequently_asked_questions": [
            "Walk me through a Python project you've built end-to-end",
            "What's a bug you've debugged in Python and how did you find it?",
            "Why do you prefer Python for certain tasks over other languages?"
        ],
        "coding_questions": [
            "Implement a LRU cache using OrderedDict or a custom doubly linked list",
            "Write a decorator that retries a function on failure up to N times",
            "Implement a generator-based pipeline that filters and transforms a large dataset lazily",
            "Write a thread-safe counter class using a Lock"
        ],
        "hr_questions": [
            "Tell me about a time you had to learn a new library or tool quickly",
            "How do you approach debugging unfamiliar code?",
            "Describe a time you optimized slow-running code"
        ],
        "system_design_questions": [
            "Design a rate limiter as a Python decorator",
            "Design a simple job queue/task scheduler using Python's concurrency primitives",
            "Design a caching layer for an API client"
        ]
    },
    "resume_tips": [
        "List specific libraries/frameworks used (FastAPI, pandas, asyncio) rather than just 'Python'",
        "Quantify impact where possible (e.g. 'reduced script runtime from 40s to 6s using multiprocessing')",
        "Include 2-3 non-trivial GitHub projects, ideally with tests and a README, not just tutorial follow-alongs",
        "Mention testing practices (pytest, coverage) if used -- it signals production-readiness",
        "Keep descriptions concrete: what the project does, what you used, one measurable result or challenge solved"
    ],
    "certifications": [
        "freeCodeCamp Scientific Computing with Python (Free)",
        "Python Institute PCEP / PCAP (Paid, widely recognized entry-level certs)",
        "Coursera Python for Everybody Specialization - University of Michigan (Paid, financial aid available)",
        "Google IT Automation with Python Professional Certificate (Paid, financial aid available)"
    ],
    "company_prep": [
        {
            "group_name": "Product Companies",
            "example_companies": ["Google", "Amazon", "Microsoft", "Meta", "Dropbox"],
            "focus_areas": ["DSA in Python", "OOP design", "System Design", "Concurrency", "Clean, idiomatic code"]
        },
        {
            "group_name": "Service Companies",
            "example_companies": ["TCS", "Infosys", "Wipro", "Accenture", "Cognizant"],
            "focus_areas": ["Aptitude", "Basic Python syntax", "Simple scripting tasks", "Communication", "Basic CS fundamentals"]
        }
    ]
}

result = db.domain_details.update_one(
    {"domain_slug": "python"},
    {"$set": doc},
    upsert=True
)

print(f"Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted ID: {result.upserted_id}")