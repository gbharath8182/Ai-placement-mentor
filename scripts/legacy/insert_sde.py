import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

DOMAIN_CARD = {
    "slug": "sde",
    "title": "Software Development Engineer (SDE)",
    "description": "Core software engineering fundamentals -- OOP, systems, databases, and APIs -- for product and service company interviews."
}

DOMAIN_DETAILS = {
    "domain_slug": "sde",
    "overview": "Software Development Engineer (SDE) is the broad, foundational engineering role most product and service companies hire for -- writing, testing, and shipping production code across the stack. Unlike a narrow specialization, SDE roles expect working competence across programming fundamentals, object-oriented design, databases, operating systems, networking, and API design, with the depth to go deeper in one area over time. This domain covers the cross-cutting engineering fundamentals that sit underneath DSA and System Design -- the practical, day-to-day skills that show up in both take-home assignments and interview loops.",
    "why_important": "Almost every entry-level and mid-level tech hiring pipeline -- product companies and service companies alike -- is built around the generalist SDE role. Even candidates who eventually specialize (backend, ML, mobile) are hired and interviewed against this same core bar first. Weakness in any one pillar (say, DBMS or OS) is a common, avoidable reason strong DSA candidates still fail final-round interviews.",
    "industries_using": [
        "Product-based technology companies",
        "IT services and consulting firms",
        "Fintech and banking technology",
        "E-commerce platforms",
        "Enterprise SaaS"
    ],
    "future_scope": "The generalist SDE role remains the largest single hiring category in tech, and is the standard launchpad into specialized tracks (backend, infra, ML platform, mobile). As AI-assisted coding tools handle more boilerplate, the fundamentals covered here -- correct OOP design, understanding what a database or OS is actually doing, designing a clean API contract -- become more valuable, not less, since they are exactly what separates an engineer who can review and reason about generated code from one who can only prompt for it.",
    "average_salary": "Rs 6-12 LPA entry-level (India, product companies), Rs 3.5-6 LPA entry-level (India, service companies) -- varies significantly by company tier and location",
    "skills_required": [
        "At least one programming language (C++, Java, or Python) at working proficiency",
        "Object-oriented programming and design",
        "Data Structures & Algorithms",
        "SQL and relational database fundamentals",
        "Operating systems and computer networks basics",
        "Version control (Git)",
        "REST API design and HTTP fundamentals",
        "Basic Linux command-line proficiency"
    ],
    "prerequisites": [
        "Programming Language (C++, Java, or Python)",
        "Basic Data Structures & Algorithms",
        "Computer fundamentals"
    ],
    "roadmap": [
        {
            "tier": "beginner",
            "items": [
                "Pick one language (C++/Java/Python) and get comfortable with its syntax and standard library",
                "Object-Oriented Programming: classes, objects, the four pillars (encapsulation, abstraction, inheritance, polymorphism)",
                "Git & GitHub: commits, branches, merges, pull requests",
                "Linux basics: filesystem navigation, permissions, common commands",
                "SQL fundamentals: SELECT/JOIN/GROUP BY, basic schema design"
            ]
        },
        {
            "tier": "intermediate",
            "items": [
                "Operating Systems: processes, threads, memory management, scheduling",
                "Computer Networks: OSI/TCP-IP model, HTTP, DNS, TCP vs UDP",
                "Database internals: indexing, normalization, transactions, ACID",
                "REST API design: resource modeling, status codes, versioning, auth",
                "Low-Level Design: SOLID principles, common design patterns"
            ]
        },
        {
            "tier": "advanced",
            "items": [
                "High-Level System Design (see the dedicated System Design domain)",
                "Deployment basics: Docker containers, CI/CD pipelines",
                "Cloud fundamentals: one major provider's core compute/storage/networking services",
                "Security fundamentals: authN vs authZ, common vulnerabilities (OWASP Top 10 awareness)",
                "Performance profiling and optimization of a real application"
            ]
        }
    ],
    "topics": [
        {
            "name": "Object-Oriented Programming (OOP)",
            "description": "The paradigm of organizing code around objects that bundle state and behavior, built on four pillars: encapsulation, abstraction, inheritance, and polymorphism.",
            "importance": "The default paradigm for almost all production codebases and the single most common non-DSA interview topic -- interviewers routinely ask candidates to design a class hierarchy live.",
            "difficulty": "beginner",
            "estimated_time": "1-2 weeks",
            "prerequisites": ["Basic programming syntax in one language"],
            "resources": {
                "documentation": "https://docs.oracle.com/javase/tutorial/java/concepts/",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLrhzvIcii6GNjpARdnO4ueTUAVR9eMBpc",
                "articles": [
                    "https://www.geeksforgeeks.org/object-oriented-programming-oops-concept-in-java/"
                ],
                "notes": "Focus on WHY each pillar exists (what problem it solves), not just definitions -- interviewers probe for this.",
                "practice_platform": "LeetCode OOP Design tag / HackerRank OOP track",
                "cheat_sheet": "Encapsulation = hide internal state; Abstraction = hide complexity behind interface; Inheritance = reuse via 'is-a'; Polymorphism = one interface, many implementations"
            },
            "practice_questions": [
                "Design a parking lot system",
                "Implement a simple Library Management System with classes for Book, Member, Loan",
                "Design a Vehicle class hierarchy (Car, Bike, Truck) demonstrating inheritance",
                "Implement an Animal class hierarchy demonstrating polymorphism",
                "Design a simple e-commerce Cart and Order class structure"
            ],
            "projects": [
                "Build a command-line library management system using classes for Book, Member, and Transaction"
            ],
            "interview_questions": [
                "What is the difference between abstraction and encapsulation?",
                "Explain composition vs inheritance -- when would you choose one over the other?",
                "What is method overloading vs method overriding?",
                "Can you have an abstract class with no abstract methods? Why would you?",
                "What is the diamond problem and how do different languages solve it?"
            ]
        },
        {
            "name": "Git & GitHub",
            "description": "Distributed version control for tracking code changes, collaborating across teams, and managing parallel lines of development through branching and merging.",
            "importance": "Universal requirement for any engineering job -- used daily, and a working knowledge is assumed rather than explicitly tested, which makes gaps embarrassing rather than forgivable.",
            "difficulty": "beginner",
            "estimated_time": "3-5 days",
            "prerequisites": ["Basic command-line comfort"],
            "resources": {
                "documentation": "https://git-scm.com/doc",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PL4cUxeGkcC9goXbgTDQ0n_4TBzOO0ocPR",
                "articles": [
                    "https://www.atlassian.com/git/tutorials"
                ],
                "notes": "Practice resolving a real merge conflict at least once -- reading about it isn't the same as doing it.",
                "practice_platform": "learngitbranching.js.org (interactive)",
                "cheat_sheet": "git add -> stage, git commit -> snapshot, git push/pull -> sync remote, git branch/checkout -> parallel work, git merge/rebase -> combine history"
            },
            "practice_questions": [
                "Walk through resolving a merge conflict in a shared file",
                "Explain the difference between git merge and git rebase",
                "What does git reset --hard vs --soft do?",
                "How do you undo a commit that's already been pushed?",
                "What is a detached HEAD state and how do you recover from it?"
            ],
            "projects": [
                "Contribute a small fix to an open-source repository via a full fork -> branch -> PR workflow"
            ],
            "interview_questions": [
                "What's the difference between git fetch and git pull?",
                "How would you undo the last commit without losing your changes?",
                "Explain what a rebase does differently from a merge, and a risk of rebasing shared branches",
                "What is .gitignore for and why does it matter?"
            ]
        },
        {
            "name": "Linux Basics",
            "description": "Command-line fluency with the Linux filesystem, permissions model, process management, and common utilities that underlie most production server environments.",
            "importance": "Most production deployments and CI/CD pipelines run on Linux; basic command-line fluency is assumed for any backend-adjacent role and often quietly tested via take-home setup instructions.",
            "difficulty": "beginner",
            "estimated_time": "1 week",
            "prerequisites": [],
            "resources": {
                "documentation": "https://www.gnu.org/software/bash/manual/bash.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLtK75qxsQaMLZSo7KL-PmiRarU7hrpnwK",
                "articles": [
                    "https://www.geeksforgeeks.org/linux-commands/"
                ],
                "notes": "Learn permissions (chmod/chown) and process management (ps, kill, top) deeply -- these come up in debugging interview scenarios.",
                "practice_platform": "OverTheWire Bandit (interactive wargame)",
                "cheat_sheet": "ls/cd/pwd -> navigate, chmod/chown -> permissions, ps/top/kill -> processes, grep/sed/awk -> text processing, curl/wget -> networking"
            },
            "practice_questions": [
                "Find all files modified in the last 24 hours in a directory tree",
                "Explain the difference between chmod 755 and chmod 644",
                "Kill a process that's hanging and not responding to normal termination",
                "Search for a string across all files in a directory recursively",
                "Explain what a symbolic link vs hard link is"
            ],
            "projects": [
                "Write a shell script that automates log rotation and archiving for a directory"
            ],
            "interview_questions": [
                "What's the difference between a process and a thread at the OS level?",
                "How do you check which process is using a specific port?",
                "Explain the Linux file permission model (owner/group/other, rwx)",
                "What does a load average of 1.0, 1.0, 1.0 mean on a single-core machine?"
            ]
        },
        {
            "name": "SQL & DBMS",
            "description": "Relational database fundamentals: schema design, normalization, SQL querying, indexing, and transaction guarantees (ACID).",
            "importance": "Nearly every backend role touches a relational database daily; SQL query-writing and schema-design questions are standard in both technical screens and take-homes.",
            "difficulty": "intermediate",
            "estimated_time": "2 weeks",
            "prerequisites": ["Basic programming fundamentals"],
            "resources": {
                "documentation": "https://www.postgresql.org/docs/current/tutorial.html",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLavw5C92dz9AmCWNC9SVN0PsSaAAB-qC6",
                "articles": [
                    "https://www.geeksforgeeks.org/sql-tutorial/"
                ],
                "notes": "Practice writing JOINs and GROUP BY queries by hand until they're automatic -- this is the most common practical SQL interview format.",
                "practice_platform": "LeetCode Database tag / SQLZoo",
                "cheat_sheet": "1NF/2NF/3NF -> normalization levels, ACID -> Atomicity/Consistency/Isolation/Durability, B-Tree index -> default index structure for range queries"
            },
            "practice_questions": [
                "Write a query to find the second-highest salary in an Employees table",
                "Find duplicate rows in a table and remove all but one copy",
                "Write a query using a self-JOIN to find employees who earn more than their manager",
                "Explain when you would denormalize a schema and why",
                "Design a normalized schema for an online bookstore (Books, Authors, Orders, Customers)"
            ],
            "projects": [
                "Design and populate a normalized schema for a hospital appointment system, then write 10 real queries against it"
            ],
            "interview_questions": [
                "What is the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN?",
                "Explain ACID properties with a real example of each",
                "What is an index, and what's the tradeoff of adding too many?",
                "What's the difference between WHERE and HAVING?",
                "Explain database normalization and give an example of a table that violates 2NF"
            ]
        },
        {
            "name": "Operating Systems",
            "description": "Core OS concepts: processes and threads, CPU scheduling, memory management (paging, virtual memory), and synchronization primitives (locks, deadlocks).",
            "importance": "A classic, near-universal product-company interview topic -- especially process vs thread, deadlocks, and memory management -- because it signals whether a candidate understands what's happening beneath their code.",
            "difficulty": "intermediate",
            "estimated_time": "2 weeks",
            "prerequisites": ["Basic programming fundamentals", "Computer fundamentals"],
            "resources": {
                "documentation": "https://pages.cs.wisc.edu/~remzi/OSTEP/",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLBlnK6fEyqRiVhbXDGLXDk_OQAeuVcp2O",
                "articles": [
                    "https://www.geeksforgeeks.org/operating-systems/"
                ],
                "notes": "Deadlock's 4 necessary conditions and how to break each one is one of the single most-repeated interview questions in this topic.",
                "practice_platform": "GeeksforGeeks OS practice section",
                "cheat_sheet": "Process = independent memory space, Thread = shares memory within a process; Deadlock needs Mutual Exclusion + Hold-and-Wait + No Preemption + Circular Wait"
            },
            "practice_questions": [
                "Explain the difference between a process and a thread with a real-world analogy",
                "What are the four necessary conditions for deadlock, and how would you prevent each?",
                "Explain the difference between paging and segmentation",
                "What is a race condition, and how do mutexes prevent it?",
                "Explain the producer-consumer problem and one way to solve it"
            ],
            "projects": [
                "Implement a simple multi-threaded producer-consumer simulation with a bounded buffer and locks"
            ],
            "interview_questions": [
                "What happens, step by step, when you run a program from the command line?",
                "Explain virtual memory and why it's useful",
                "What's the difference between a mutex and a semaphore?",
                "Describe two common CPU scheduling algorithms and their tradeoffs",
                "What is thrashing, and what causes it?"
            ]
        },
        {
            "name": "Computer Networks",
            "description": "How data moves across networks: the OSI and TCP/IP models, HTTP request/response lifecycle, TCP vs UDP, and DNS resolution.",
            "importance": "Directly relevant to how every web application and API actually works; a frequent interview topic for backend and full-stack roles, and unavoidable once debugging real production network issues.",
            "difficulty": "intermediate",
            "estimated_time": "1-2 weeks",
            "prerequisites": ["Basic programming fundamentals"],
            "resources": {
                "documentation": "https://developer.mozilla.org/en-US/docs/Web/HTTP",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLIFyRwBY_4bRLmKfP1KnZA_2UZbcoOUcw",
                "articles": [
                    "https://www.geeksforgeeks.org/computer-network-tutorials/"
                ],
                "notes": "Be able to trace what happens end-to-end when you type a URL and hit Enter -- this exact question is asked constantly.",
                "practice_platform": "GeeksforGeeks Computer Networks practice section",
                "cheat_sheet": "TCP = reliable, ordered, connection-based; UDP = fast, unordered, connectionless; HTTP status: 2xx success, 3xx redirect, 4xx client error, 5xx server error"
            },
            "practice_questions": [
                "Walk through what happens when you type a URL into a browser and press Enter",
                "Explain the difference between TCP and UDP, and give a real use case for each",
                "What is the TCP three-way handshake?",
                "Explain the difference between HTTP and HTTPS",
                "What is DNS and how does resolution work step by step?"
            ],
            "projects": [
                "Build a simple raw TCP client-server chat application to observe the handshake and data flow directly"
            ],
            "interview_questions": [
                "What's the difference between HTTP/1.1 and HTTP/2?",
                "Explain the OSI model layers briefly",
                "What is a CDN and how does it reduce latency?",
                "What's the difference between a forward proxy and a reverse proxy?",
                "How does HTTPS establish a secure connection (TLS handshake, high level)?"
            ]
        },
        {
            "name": "REST APIs",
            "description": "Designing and consuming RESTful web services: resource modeling, HTTP verbs, status codes, statelessness, versioning, and authentication.",
            "importance": "REST is the default interface between frontend and backend (and between services) in the overwhelming majority of production systems -- both designing and correctly consuming APIs is a daily skill, and API design questions are common in take-home assignments.",
            "difficulty": "intermediate",
            "estimated_time": "1 week",
            "prerequisites": ["Computer Networks basics", "Basic programming fundamentals"],
            "resources": {
                "documentation": "https://restfulapi.net/",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLillGF-RfqbYE6Ik_EuXA2iZFcE082B3s",
                "articles": [
                    "https://www.geeksforgeeks.org/rest-api-introduction/"
                ],
                "notes": "Practice designing a REST API for a real product (e.g. a bookstore) end-to-end: resource names, verbs, status codes, and pagination -- not just reading definitions.",
                "practice_platform": "Postman API design exercises / build against a mock API with json-server",
                "cheat_sheet": "GET = read, POST = create, PUT = replace, PATCH = partial update, DELETE = remove; 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Server Error"
            },
            "practice_questions": [
                "Design REST endpoints for a bookstore API (list, get, create, update, delete books)",
                "What status code should a successful POST that creates a resource return, and what else should the response include?",
                "How would you design pagination for an endpoint returning thousands of records?",
                "Explain the difference between PUT and PATCH with an example",
                "How would you version a public REST API without breaking existing clients?"
            ],
            "projects": [
                "Build a REST API for a task-manager app with full CRUD, pagination, and basic token authentication"
            ],
            "interview_questions": [
                "What makes an API 'RESTful' -- what are the constraints?",
                "Why is statelessness important in REST API design?",
                "How would you handle authentication in a REST API (session vs token-based)?",
                "What's the difference between a 401 and a 403 response?",
                "How would you design an endpoint for uploading a large file?"
            ]
        },
        {
            "name": "Low-Level Design (LLD)",
            "description": "Translating a feature or system requirement into concrete class diagrams, applying SOLID principles and common design patterns to produce maintainable, extensible object-oriented code.",
            "importance": "The direct next step after OOP fundamentals, and a distinct interview round at most product companies (separate from DSA and HLD) -- candidates are asked to design a class structure for something like a parking lot or elevator system live on a whiteboard.",
            "difficulty": "advanced",
            "estimated_time": "2-3 weeks",
            "prerequisites": ["Object-Oriented Programming (OOP)"],
            "resources": {
                "documentation": "https://refactoring.guru/design-patterns",
                "youtube_playlist": "https://www.youtube.com/playlist?list=PLmzKr0aXwzL2fmi5iWnT7yhz3H2Ovm5xE",
                "articles": [
                    "https://www.geeksforgeeks.org/system-design-low-level-design-lld/"
                ],
                "notes": "Practice drawing the class diagram BEFORE writing any code for each LLD problem -- interviewers grade the design process, not just a working final answer.",
                "practice_platform": "GeeksforGeeks LLD practice problems",
                "cheat_sheet": "SOLID: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion; common patterns: Singleton, Factory, Observer, Strategy, Decorator"
            },
            "practice_questions": [
                "Design a parking lot system with multiple vehicle types and floors",
                "Design an elevator system for a multi-floor building",
                "Design a simplified version of Splitwise (expense-sharing)",
                "Design a Tic-Tac-Toe game engine supporting arbitrary board sizes",
                "Design a vending machine state machine"
            ],
            "projects": [
                "Fully implement a runnable parking lot system in your chosen language, including class diagram, from a written requirements doc"
            ],
            "interview_questions": [
                "Explain the Single Responsibility Principle with an example of a class that violates it",
                "What's the difference between the Strategy and Factory design patterns?",
                "When would you use composition over inheritance in an LLD problem?",
                "Explain the Observer pattern and a real system that uses it",
                "How do you decide what should be an interface vs an abstract class in your design?"
            ]
        }
    ],
    "skills": [
        {
            "name": "Object-Oriented Design",
            "description": "Translating requirements into clean, extensible class structures using OOP principles and design patterns.",
            "importance": "Directly tested in LLD interview rounds and required for any maintainable production codebase.",
            "level": "intermediate",
            "estimated_hours": 25
        },
        {
            "name": "SQL Querying",
            "description": "Writing correct, efficient SQL queries including joins, aggregations, and subqueries.",
            "importance": "Daily requirement for most backend roles; a near-universal interview topic.",
            "level": "intermediate",
            "estimated_hours": 20
        },
        {
            "name": "Version Control (Git)",
            "description": "Managing code history, branches, and collaboration workflows with Git and GitHub.",
            "importance": "Used in every professional engineering job from day one.",
            "level": "beginner",
            "estimated_hours": 8
        },
        {
            "name": "API Design",
            "description": "Designing clean, versioned, well-documented REST APIs that are easy for other engineers to consume.",
            "importance": "Core skill for backend and full-stack roles; frequently assessed via take-home assignments.",
            "level": "intermediate",
            "estimated_hours": 15
        },
        {
            "name": "Linux Command-Line Proficiency",
            "description": "Navigating, scripting, and debugging in a Linux shell environment.",
            "importance": "Most production and CI/CD environments run on Linux; assumed baseline skill.",
            "level": "beginner",
            "estimated_hours": 10
        }
    ],
    "practice_platforms": [
        "LeetCode",
        "GeeksforGeeks",
        "HackerRank",
        "InterviewBit",
        "Pramp (mock interviews)"
    ],
    "projects": [
        {
            "title": "Task Manager REST API",
            "description": "A full CRUD REST API for managing tasks, with user authentication and pagination.",
            "skills_learned": ["REST API design", "SQL schema design", "Authentication basics"],
            "technologies_used": ["Python/Java + a web framework", "PostgreSQL or MySQL"],
            "github_ideas": ["task-manager-rest-api"],
            "tier": "beginner"
        },
        {
            "title": "Custom Version Control Simulator",
            "description": "A simplified command-line tool that mimics core Git operations (init, commit, branch, merge) to understand what Git is doing internally.",
            "skills_learned": ["File system operations", "Data structures for history tracking", "CLI design"],
            "technologies_used": ["Python or Java"],
            "github_ideas": ["mini-git-simulator"],
            "tier": "intermediate"
        },
        {
            "title": "Multi-threaded Job Scheduler",
            "description": "A job scheduler that queues and executes tasks across worker threads with proper synchronization, demonstrating OS-level concurrency concepts in application code.",
            "skills_learned": ["Multithreading", "Synchronization primitives", "Producer-consumer pattern"],
            "technologies_used": ["Java (java.util.concurrent) or Python (threading/asyncio)"],
            "github_ideas": ["concurrent-job-scheduler"],
            "tier": "intermediate"
        },
        {
            "title": "Parking Lot Management System (Full LLD + Backend)",
            "description": "A complete, real-world LLD exercise: design and implement a parking lot system with multiple vehicle types, floors, and pricing, exposed via a REST API and backed by a real database.",
            "skills_learned": ["Low-Level Design", "SOLID principles", "REST API design", "Database schema design"],
            "technologies_used": ["Java or Python", "PostgreSQL", "REST framework"],
            "github_ideas": ["parking-lot-system"],
            "tier": "advanced"
        }
    ],
    "interview_prep": {
        "important_topics": [
            "Object-Oriented Programming & SOLID principles",
            "SQL and database fundamentals",
            "Operating Systems (processes, threads, deadlocks, memory)",
            "Computer Networks (HTTP, TCP/UDP, DNS)",
            "Low-Level Design patterns"
        ],
        "frequently_asked_questions": [
            "Walk me through a project you built end-to-end",
            "What was the most challenging bug you've debugged and how did you find it?",
            "Why do you want to work here?"
        ],
        "coding_questions": [
            "Design and implement a thread-safe LRU cache",
            "Implement a simple key-value store with expiring keys",
            "Write a function to detect a deadlock in a resource allocation graph",
            "Implement a rate limiter (token bucket algorithm)"
        ],
        "hr_questions": [
            "Tell me about a time you disagreed with a teammate's technical decision",
            "How do you handle tight deadlines?",
            "Where do you see yourself in the next few years?"
        ],
        "system_design_questions": [
            "Design a URL shortener",
            "Design a simplified Splitwise",
            "Design a parking lot system (LLD)",
            "Design a notification service"
        ]
    },
    "resume_tips": [
        "List specific technologies (language, framework, database) rather than vague terms like 'worked with backend systems'",
        "Quantify project impact where possible (e.g. 'reduced query time by 40%' beats 'optimized database queries')",
        "Include a GitHub link with at least 2-3 well-documented, non-trivial projects -- not just tutorial clones",
        "Mention any exposure to Git workflows, code review, or CI/CD, since these signal production readiness beyond coursework",
        "Keep project descriptions to 2-3 lines each: what it does, what you used, one concrete result or challenge solved"
    ],
    "certifications": [
        "AWS Certified Cloud Practitioner (paid, beginner-friendly, widely recognized)",
        "freeCodeCamp Backend Development certifications (free)",
        "Oracle Certified Associate Java Programmer (paid, language-specific)",
        "Google IT Support Professional Certificate (free/paid tiers, foundational)"
    ],
    "company_prep": [
        {
            "group_name": "Product Companies",
            "example_companies": ["Google", "Microsoft", "Amazon", "Adobe", "Atlassian"],
            "focus_areas": ["DSA depth", "Low-Level Design", "System Design", "Operating Systems", "DBMS", "Computer Networks"]
        },
        {
            "group_name": "Service Companies",
            "example_companies": ["TCS", "Infosys", "Wipro", "Accenture", "Cognizant"],
            "focus_areas": ["Aptitude", "SQL", "Core programming fundamentals", "Communication", "Basic CS fundamentals (OS, DBMS, Networks)"]
        }
    ]
}

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    # Safe to re-run: retain the platform card if it already exists and
    # refresh the detailed SDE curriculum in place.
    r1 = await db.domains.update_one({"slug": "sde"}, {"$set": DOMAIN_CARD}, upsert=True)
    print("Domain card matched/modified:", r1.matched_count, r1.modified_count)

    r2 = await db.domain_details.update_one(
        {"domain_slug": "sde"}, {"$set": DOMAIN_DETAILS}, upsert=True
    )
    print("Detailed curriculum matched/modified:", r2.matched_count, r2.modified_count)

    print("Topics count:", len(DOMAIN_DETAILS["topics"]))
    print("SUCCESS")

asyncio.run(main())
