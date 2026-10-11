"""Seed the dashboard-visible SDE curriculum.

This is intentionally separate from ``insert_sde.py``: domain_details drives
the extended roadmap and Mock Interview, while the Dashboard reads the
``topics`` collection. Safe to run repeatedly.
"""
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings


REFERENCES = {
    "programming": ("Code Complete, 2nd ed. — Steve McConnell", "https://www.microsoftpressstore.com/store/code-complete-9780735619678"),
    "oop": ("Object-Oriented Analysis and Design with Applications — Grady Booch", "https://www.informit.com/store/object-oriented-analysis-and-design-with-applications-9780201895513"),
    "dsa": ("Introduction to Algorithms, 4th ed. — Cormen, Leiserson, Rivest, Stein", "https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/"),
    "git": ("Pro Git, 2nd ed. — Scott Chacon & Ben Straub", "https://git-scm.com/book/en/v2"),
    "os": ("Operating System Concepts, 10th ed. — Silberschatz, Galvin, Gagne", "https://www.os-book.com/OS10/"),
    "dbms": ("Database System Concepts, 7th ed. — Silberschatz, Korth, Sudarshan", "https://www.db-book.com/"),
    "networks": ("Computer Networking: A Top-Down Approach — Kurose & Ross", "https://gaia.cs.umass.edu/kurose_ross/"),
    "api": ("Web API Design — Brian Mulloy", "https://cloud.google.com/files/apigee/apigee-web-api-design-the-missing-link-ebook.pdf"),
    "testing": ("The Art of Software Testing, 3rd ed. — Myers, Sandler, Badgett", "https://onlinelibrary.wiley.com/doi/book/10.1002/9781119202486"),
    "design": ("Head First Design Patterns, 2nd ed. — Freeman & Robson", "https://www.oreilly.com/library/view/head-first-design/9781492077992/"),
}

# One visual mental model per topic. These are deliberately concise: the
# lesson explains the details; the diagram gives learners the structure first.
DIAGRAMS = {
    "sde-programming-foundations": "flowchart LR\nRequirement --> Decompose\nDecompose --> Implement\nImplement --> Test_edges[Check edge cases]\nTest_edges --> Refactor",
    "sde-oop-solid": "classDiagram\nclass Client\nclass Service { +execute() }\nclass Repository { +save() }\nClient --> Service\nService --> Repository",
    "sde-data-structures-complexity": "flowchart LR\nProblem --> Access_pattern\nAccess_pattern --> Hash_table\nAccess_pattern --> Ordered_structure\nAccess_pattern --> Queue_or_heap[Queue or heap]\nHash_table --> Measure",
    "sde-git-collaboration": "gitGraph\ncommit id: \"main\"\nbranch feature\ncheckout feature\ncommit id: \"small change\"\ncommit id: \"tests\"\ncheckout main\nmerge feature",
    "sde-operating-systems": "flowchart LR\nRequest --> Thread\nThread --> Scheduler\nScheduler --> CPU\nThread --> IO_wait[I/O wait]\nIO_wait --> Scheduler",
    "sde-dbms-sql": "erDiagram\nUSER ||--o{ ENROLLMENT : has\nCOURSE ||--o{ ENROLLMENT : contains\nUSER { string id }\nCOURSE { string id }\nENROLLMENT { string user_id }",
    "sde-computer-networks": "sequenceDiagram\nBrowser->>DNS: resolve name\nDNS-->>Browser: IP address\nBrowser->>Server: TLS + HTTP request\nServer-->>Browser: HTTP response",
    "sde-rest-api-backend": "flowchart LR\nClient --> Controller\nController --> Service\nService --> Repository\nRepository --> Database\nService --> Metrics",
    "sde-testing-quality": "flowchart TB\nUnit_tests --> Integration_tests\nIntegration_tests --> End_to_end\nEnd_to_end --> Monitoring\nMonitoring --> Incident_learning",
    "sde-lld-design-patterns": "flowchart LR\nRequirements --> Domain_model\nDomain_model --> Interfaces\nInterfaces --> Invariants\nInvariants --> Tests\nTests --> Tradeoffs",
}


TOPICS = [
    ("sde-programming-foundations", "Programming Foundations & Code Quality", "beginner", "programming", [
        ("Program structure, types, and control flow", "Translate a requirement into small, readable functions with clear input, output, and failure behavior. Understand value vs reference semantics, scope, lifetime, and the cost of common operations in the language you interview in.", ["Trace execution before debugging", "Choose names that reveal intent", "Keep functions focused on one responsibility"], "Explain how you would diagnose a function that works for normal inputs but fails at a boundary value."),
        ("Defensive programming and error handling", "Production code treats invalid input, unavailable dependencies, and partial failure as normal possibilities. Validate at boundaries, return useful errors, and never silently hide a failure that a caller must handle.", ["Validate external input early", "Separate expected errors from programmer bugs", "Preserve context in logs and error messages"], "When should an API reject a request, retry it, or return a partial result?"),
        ("Complexity and resource awareness", "An SDE must estimate time and space before a service becomes slow. Big-O describes growth, while real performance also depends on allocation, I/O, cache locality, and network round trips.", ["Recognize nested-loop and repeated-query traps", "Measure before optimizing", "State time and space complexity for key paths"], "Compare a linear scan, hash lookup, and database index for a hot lookup path."),
        ("Readable, maintainable code", "Maintainability comes from simple control flow, meaningful boundaries, and tests that make safe change possible. Refactoring improves structure without changing observable behavior.", ["Prefer composition over deeply coupled code", "Remove duplication after understanding it", "Use comments to explain why, not what"], "Refactor a long method without changing its behavior; what tests protect you?"),
    ]),
    ("sde-oop-solid", "Object-Oriented Design & SOLID", "beginner", "oop", [
        ("Encapsulation, abstraction, inheritance, polymorphism", "Objects should protect their invariants and expose behavior rather than mutable implementation details. Abstraction lets callers depend on a stable contract while implementations change.", ["Define responsibilities before classes", "Keep representation private", "Use polymorphism to remove type-switching"], "Why is exposing a mutable collection from a class risky?"),
        ("Relationships and composition", "Association, aggregation, and composition describe ownership and lifetime. Prefer composing small collaborators when an is-a relationship is not genuinely substitutable.", ["Model ownership explicitly", "Avoid inheritance only for code reuse", "Inject dependencies that vary"], "Model an order, its line items, and a payment service. Which objects own which?"),
        ("SOLID principles", "SOLID is a set of pressures toward changeable code: one reason to change, extension through stable interfaces, substitutable implementations, focused interfaces, and dependency inversion.", ["Single responsibility", "Open/closed through extension points", "Depend on abstractions at boundaries"], "Show how an interface can prevent a notification module from becoming a giant conditional."),
        ("Contracts, invariants, and object design", "A class contract states what callers may assume and what they must provide. Invariants are conditions that remain true after every public operation, such as a bank balance never dropping below an allowed limit.", ["Write preconditions and postconditions", "Guard state transitions", "Make invalid states hard to represent"], "What invariants belong in a seat-reservation object under concurrent requests?"),
    ]),
    ("sde-data-structures-complexity", "Data Structures, Algorithms & Complexity", "intermediate", "dsa", [
        ("Choosing the right data structure", "Arrays, linked structures, hash tables, heaps, trees, and graphs optimize different operations. Choose from the access pattern and constraints, not from familiarity.", ["Map operations to costs", "Consider ordering and duplicate needs", "Account for memory overhead"], "Pick structures for an LRU cache and justify each component."),
        ("Searching, sorting, and hashing", "Binary search needs a monotonic predicate; sorting can turn expensive repeated work into one preprocessing step. Hash tables offer expected constant-time access but depend on equality, hashing, and load factor.", ["State assumptions before binary search", "Know stable versus unstable sort", "Handle hash collisions conceptually"], "When is sorting first faster than repeatedly searching an unsorted collection?"),
        ("Recursion, iteration, and dynamic programming", "Recursion mirrors recursive structure but uses stack space. Dynamic programming converts repeated subproblems into stored results after defining state, transition, base cases, and evaluation order.", ["Draw a recursion tree", "Identify overlapping subproblems", "Optimize memory only after correctness"], "Derive a DP state for minimum cost to reach the end of an array."),
        ("Correctness and edge cases", "A convincing solution explains why it works, not only why it passes an example. Use loop invariants, counterexamples, and boundaries such as empty input, duplicates, overflow, and one-element cases.", ["State an invariant", "Test smallest and largest valid inputs", "Separate correctness from complexity"], "Give a loop invariant for two-pointer duplicate removal."),
    ]),
    ("sde-git-collaboration", "Git, GitHub & Engineering Collaboration", "beginner", "git", [
        ("Commits, branches, and history", "A commit is a snapshot with parents; a branch is a movable reference to a commit. Small, coherent commits make review, bisecting, and rollback practical.", ["Commit one logical change at a time", "Use descriptive commit messages", "Keep the main branch releasable"], "Explain the difference between merging and rebasing, including the history trade-off."),
        ("Pull requests and code review", "A pull request communicates intent, scope, tests, and risk. Good reviews check behavior, maintainability, security, and tests while keeping comments specific and respectful.", ["Write a concise PR description", "Review the diff before style", "Ask questions before assuming intent"], "What would you look for when reviewing a change to authentication middleware?"),
        ("Merge conflicts and recovery", "Conflicts mean Git cannot safely choose between changes. Resolve them by understanding both intents, test the result, and use reflog or revert rather than panic when history needs recovery.", ["Resolve conflicts deliberately", "Never force-push shared history casually", "Use revert for safe production rollback"], "A bad change reached main. Compare reverting, resetting, and a hotfix commit."),
        ("CI/CD and release discipline", "Continuous integration runs automated checks on each change; delivery keeps software deployable; deployment releases automatically. A pipeline is only useful when failures are actionable and protected branches enforce it.", ["Run lint, unit, integration checks", "Protect secrets in environment variables", "Use staged rollout and rollback plans"], "What checks should block a backend change from merging?"),
    ]),
    ("sde-operating-systems", "Operating Systems, Processes & Concurrency", "intermediate", "os", [
        ("Processes, threads, and context switching", "A process has an isolated address space and resources; threads share a process address space. The scheduler multiplexes CPUs by context switching, which has overhead and affects latency.", ["Distinguish isolation from parallelism", "Know user versus kernel mode", "Relate thread count to workload type"], "When would you choose processes over threads for a service?"),
        ("Memory, virtual memory, and allocation", "Virtual memory gives each process an address-space abstraction backed by RAM and storage. Pages, page faults, stack, heap, and garbage collection explain many performance and crash symptoms.", ["Stack versus heap lifetime", "Recognize paging pressure", "Avoid unnecessary allocation on hot paths"], "Why can a program be slow even when CPU utilization is low during heavy paging?"),
        ("Synchronization and race conditions", "A race occurs when result depends on timing of unsafely shared operations. Locks, semaphores, atomics, and message passing coordinate work; every choice trades simplicity, throughput, and liveness.", ["Protect compound read-modify-write", "Minimize lock scope", "Avoid lock-order cycles"], "Two requests decrement the last inventory item. How do you prevent overselling?"),
        ("Deadlock, starvation, and async I/O", "Deadlock requires mutual exclusion, hold-and-wait, no preemption, and circular wait. Async I/O lets a thread do other work while a slow operation waits, but does not make CPU-bound work free.", ["Use timeouts and cancellation", "Define lock ordering", "Separate CPU-bound work from I/O-bound work"], "Why can adding more threads make a database-backed service slower?"),
    ]),
    ("sde-dbms-sql", "DBMS, SQL & Data Modeling", "intermediate", "dbms", [
        ("Relational modeling and normalization", "A relational model represents facts in tables linked by keys. Normalization reduces update anomalies; deliberate denormalization can speed read-heavy queries when consistency is managed.", ["Choose primary and foreign keys", "Model one-to-many and many-to-many relations", "Document ownership of each fact"], "Design tables for users, courses, and enrollments."),
        ("SQL querying and joins", "SQL is declarative: specify the result, and the optimizer chooses a plan. Inner and outer joins combine related sets; grouping and window functions summarize without moving data into application code.", ["Filter early", "Use parameterized queries", "Understand join cardinality"], "Write and explain a query for users with no completed applications."),
        ("Indexes and query plans", "An index speeds selected access patterns at the cost of write work and storage. Composite index column order matters; use an explain plan to see whether the engine actually uses an index.", ["Index selective predicates", "Avoid indexing every column", "Watch for N+1 query patterns"], "Why might an index not improve a query that returns most rows?"),
        ("Transactions, isolation, and recovery", "Transactions provide atomicity, consistency, isolation, and durability. Isolation levels determine which concurrent anomalies are possible, while logs and recovery preserve durability after crashes.", ["Keep transactions short", "Use constraints for invariants", "Know dirty, non-repeatable, and phantom reads"], "How would you transfer money between accounts safely?"),
    ]),
    ("sde-computer-networks", "Computer Networks, HTTP & Web Security", "intermediate", "networks", [
        ("TCP/IP and the request path", "A web request crosses layers: DNS resolves a name, TCP or QUIC establishes transport, TLS protects the channel, HTTP carries the message, and routers move packets between networks.", ["Explain IP versus port", "Distinguish latency from bandwidth", "Trace a request end to end"], "Walk through what happens after entering a secure URL in a browser."),
        ("HTTP methods, status codes, and caching", "HTTP defines uniform methods and response semantics. Correct status codes improve clients and observability; caching headers allow safe reuse when freshness rules are explicit.", ["Use GET only for safe reads", "Know 2xx, 4xx, and 5xx meanings", "Understand Cache-Control and ETag"], "When should an update be PUT versus PATCH, and how would you prevent duplicate retries?"),
        ("TLS, authentication, and authorization", "TLS protects data in transit but does not decide identity or permission. Authentication establishes who the caller is; authorization checks what that caller can do for each resource.", ["Hash passwords with a slow password hash", "Validate tokens and expiry", "Apply least privilege"], "Why is hiding a button not authorization?"),
        ("Common web vulnerabilities", "Input crosses trust boundaries. Prevent injection with parameterized queries, cross-site scripting with output encoding and safe DOM APIs, and request forgery with appropriate token/origin defenses.", ["Never trust client input", "Keep secrets out of frontend bundles", "Log security events without leaking data"], "Describe how you would secure a file-upload endpoint."),
    ]),
    ("sde-rest-api-backend", "Backend Engineering & REST API Design", "intermediate", "api", [
        ("Resources, endpoints, and contracts", "A REST-style API exposes stable resource-oriented contracts. A contract includes URL shape, request validation, response schema, pagination, error semantics, and compatibility expectations.", ["Name resources with nouns", "Version deliberately", "Validate and document request/response shapes"], "Design endpoints for applications, interviews, and feedback."),
        ("Service layering and dependencies", "Keep transport concerns, business rules, and persistence concerns separate so each can be tested and changed independently. Dependency injection makes external systems replaceable in tests.", ["Controllers translate HTTP", "Services enforce business rules", "Repositories isolate data access"], "Where should duplicate-email validation live and why?"),
        ("Reliability, idempotency, and observability", "Networks fail and clients retry. Idempotency keys prevent duplicated side effects; timeouts, retries with backoff, correlation IDs, metrics, and structured logs make failures visible and manageable.", ["Set deadlines for outbound calls", "Retry only safe operations", "Measure error rate and latency"], "How would you make payment creation safe when a client retries after a timeout?"),
        ("Scaling stateful services", "Stateless application instances can scale horizontally when shared state lives in a database, cache, or durable queue. Rate limits, queues, and backpressure protect dependencies from overload.", ["Avoid in-memory session dependence", "Use pagination for large results", "Plan graceful degradation"], "A popular endpoint overloads the database. What would you inspect and change first?"),
    ]),
    ("sde-testing-quality", "Testing, Debugging & Reliability", "intermediate", "testing", [
        ("Test levels and the testing pyramid", "Unit tests isolate small behavior, integration tests verify component boundaries, and end-to-end tests validate critical journeys. Balance speed, confidence, and maintenance rather than relying on one test type.", ["Test behavior, not private implementation", "Use realistic integration boundaries", "Keep end-to-end tests focused"], "Which tests would you add for user registration and why?"),
        ("Test design and edge cases", "Good tests partition inputs into meaningful classes and target boundaries where behavior changes. Equivalence classes, boundary-value analysis, and property-based thinking expose defects normal examples miss.", ["Test empty, null, min, max, duplicate cases", "Name tests by behavior", "Make failure messages diagnostic"], "Create a compact test plan for a password validator."),
        ("Debugging systematically", "Debugging starts with a reproducible symptom, then narrows hypotheses using logs, metrics, traces, a debugger, and a minimal failing case. Avoid changing several variables at once.", ["Reproduce before fixing", "Inspect recent changes", "Verify the fix with a regression test"], "Production errors increased after deployment. What is your first 30-minute investigation plan?"),
        ("Reliability and incident thinking", "Reliability is a product feature. Define service-level indicators, error budgets, alerts that require action, and post-incident reviews that improve systems rather than blame people.", ["Alert on symptoms users feel", "Use feature flags and canaries", "Write actionable runbooks"], "What belongs in a useful incident postmortem?"),
    ]),
    ("sde-lld-design-patterns", "Low-Level Design & Design Patterns", "advanced", "design", [
        ("From requirements to domain model", "Low-level design turns use cases and constraints into collaborating objects, interfaces, state transitions, and persistence boundaries. Start with behavior and invariants before drawing class diagrams.", ["Clarify functional and non-functional needs", "Identify entities and value objects", "Model state transitions"], "Design a library system that supports borrowing, return, and overdue rules."),
        ("Creational and structural patterns", "Factory, builder, adapter, decorator, and facade patterns solve recurring construction and integration problems. A pattern is useful only when it reduces a real source of coupling or complexity.", ["Use factories for varying construction", "Use adapters at external boundaries", "Avoid pattern ceremony without a need"], "When would a factory be clearer than a long constructor with flags?"),
        ("Behavioral patterns and extensibility", "Strategy, observer, command, and state let behavior vary without central conditional logic. They are especially useful where new policies or workflows should be added with minimal modification.", ["Prefer a strategy for replaceable policies", "Avoid synchronous observer cascades", "Make state transitions explicit"], "Model multiple discount rules that can be added independently."),
        ("Concurrency, persistence, and trade-offs", "A good design accounts for transaction boundaries, concurrent updates, failure recovery, and performance—not only class diagrams. State the trade-off behind every major choice.", ["Protect invariants across repositories", "Use optimistic locking where conflicts are rare", "Keep interfaces small and testable"], "Extend a parking-lot design to handle two simultaneous reservations for the final spot."),
    ]),
]


def make_subtopic(title, body, bullets, interview, reference, diagram=None):
    ref_label, ref_url = REFERENCES[reference]
    blocks = [
        {"type": "heading", "level": 2, "value": title},
        {"type": "text", "value": body},
        {"type": "heading", "level": 3, "value": "What to master"},
        {"type": "list", "items": bullets, "ordered": False},
        {"type": "callout", "kind": "important", "title": "Interview lens", "value": interview},
    ]
    if diagram:
        blocks.append({"type": "diagram", "title": "Concept map", "value": diagram})
    blocks.extend([
        {
            "type": "knowledge_check",
            "question": f"Before applying {title.lower()}, what is the most useful first step?",
            "options": [
                "State the inputs, constraints, and success condition.",
                "Start coding the longest method immediately.",
                "Copy a solution without checking its assumptions.",
            ],
            "correct_index": 0,
            "explanation": "Strong engineers make the problem and its constraints explicit before choosing an implementation.",
        },
        {"type": "resource_link", "label": f"Reference: {ref_label}", "url": ref_url},
    ])
    return {
        "title": title,
        "content_blocks": blocks,
    }


async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]
    await db.domains.update_one(
        {"slug": "sde"},
        {"$set": {"slug": "sde", "title": "Software Development Engineer (SDE)", "description": "A textbook-informed SDE path covering programming, CS foundations, backend engineering, quality, and low-level design."}},
        upsert=True,
    )
    for slug, title, difficulty, reference, subtopics in TOPICS:
        topic = {
            "domain_slug": "sde", "slug": slug, "title": title, "difficulty": difficulty,
            "subtopics": [
                make_subtopic(*subtopic, reference, DIAGRAMS[slug] if index == 0 else None)
                for index, subtopic in enumerate(subtopics)
            ],
        }
        await db.topics.update_one({"slug": slug}, {"$set": topic}, upsert=True)
    print(f"Seeded {len(TOPICS)} SDE topics with {sum(len(item[4]) for item in TOPICS)} subtopics.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
