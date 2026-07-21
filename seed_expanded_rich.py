import asyncio
import sys
import os
sys.path.insert(0, r"c:\Users\navaneeth\Ai-placement-mentor")
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

DOMAINS = {
    "cloud-devops": {
        "title": "Cloud, DevOps & SRE",
        "description": "Build, ship, observe, and operate reliable software in modern cloud environments.",
        "topics": [
            {
                "slug": "cloud-devops-linux-networking",
                "title": "Linux, Networking & Shell",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Process Management & System Resource Inspection",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Understanding Linux Processes"},
                            {"type": "text", "value": "Linux runs tasks as **processes**, each assigned a unique Process ID (PID). The kernel allocates isolated virtual memory and resources to each process. As a DevOps engineer, you must know how to inspect resource consumption and coordinate process signals to debug memory leaks and CPU spikes."},
                            {"type": "code", "language": "bash", "value": "# List active processes sorted by memory usage\nps aux --sort=-%mem | head -n 10\n\n# Gracefully terminate process 1234, or force kill if non-responsive\nkill -15 1234\nkill -9 1234"},
                            {"type": "callout", "kind": "important", "title": "SIGTERM vs SIGKILL", "value": "SIGTERM (15) asks a process to clean up and shut down gracefully (close file handles, finish current transactions). SIGKILL (9) abruptly halts the process at the OS level, risking corrupt files or data leakage."},
                            {"type": "knowledge_check", "question": "Which signal is sent by the `kill -9` command?", "options": [
                                "SIGTERM",
                                "SIGKILL",
                                "SIGINT"
                            ], "correct_index": 1, "explanation": "kill -9 sends the SIGKILL signal, which terminates the process immediately without cleanup."}
                        ]
                    },
                    {
                        "title": "Network Troubleshooting: Sockets, Ports & DNS",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Diagnosing Network Connectivity"},
                            {"type": "text", "value": "Services bind to sockets containing an IP address and a Port. Troubleshooting networking issues requires isolating the layer of failure: DNS resolution (converting names to IPs), connection handshakes (TCP/IP routing), or application protocol negotiations (HTTP/TLS)."},
                            {"type": "code", "language": "bash", "value": "# Check DNS resolution for a domain\nnslookup github.com\n\n# Verify if port 8000 is listening locally\nnetstat -ano | grep 8000\n\n# Test TCP handshake with external server port\ncurl -v telnet://1.1.1.1:53"},
                            {"type": "callout", "kind": "tip", "title": "Tool Selection", "value": "Use `ping` to test raw ICMP routing, `nslookup`/`dig` to verify DNS, and `curl`/`telnet` to check if a specific TCP port is open and accepting traffic."},
                            {"type": "knowledge_check", "question": "Which tool would you use to verify if a remote server is listening on port 443?", "options": [
                                "ping",
                                "nslookup",
                                "curl or telnet"
                            ], "correct_index": 2, "explanation": "ping only tests ICMP echo requests; curl or telnet attempts a TCP connection handshake on a specific port."}
                        ]
                    }
                ]
            },
            {
                "slug": "cloud-devops-containers",
                "title": "Containers & Docker",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Docker Architecture & Layers",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Containerization vs. Virtualization"},
                            {"type": "text", "value": "Unlike Virtual Machines which require a full guest OS, **containers** share the host system's kernel. They use Linux **Namespaces** (for resource isolation: network, process tree, mount points) and **Control Groups** (cgroups, for resource limits: CPU, memory). Docker builds images using a read-only union file system composed of cached execution layers."},
                            {"type": "diagram", "title": "Containers vs VMs", "value": "flowchart TD\n    subgraph VM[Virtual Machine]\n        App1[App] --> GuestOS[Guest OS]\n        GuestOS --> Hypervisor[Hypervisor]\n    end\n    subgraph Container[Docker Container]\n        App2[App] --> Engine[Docker Engine]\n        Engine --> HostKernel[Host Kernel]\n    end"},
                            {"type": "code", "language": "dockerfile", "value": "# Example multi-stage build to reduce image size\nFROM python:3.11-slim AS builder\nWORKDIR /app\nRUN pip install --user requests\n\nFROM python:3.11-slim\nWORKDIR /app\nCOPY --from=builder /root/.local /root/.local\nENV PATH=/root/.local/bin:$PATH\nCMD [\"python\", \"app.py\"]"},
                            {"type": "callout", "kind": "important", "title": "Multi-stage Builds", "value": "Multi-stage builds allow separating compiling tools (like gcc, npm install) from the final runtime image, drastically reducing the attack surface and image size."},
                            {"type": "knowledge_check", "question": "Which Linux kernel feature enforces memory and CPU limits on a container?", "options": [
                                "Namespaces",
                                "Control Groups (cgroups)",
                                "Union File System"
                            ], "correct_index": 1, "explanation": "cgroups (Control Groups) restrict and monitor resource limits like memory, CPU, and network bandwidth for processes."}
                        ]
                    }
                ]
            },
            {
                "slug": "cloud-devops-cicd",
                "title": "CI/CD & Release Engineering",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Continuous Integration Pipelines",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Automating Code Quality Gates"},
                            {"type": "text", "value": "Continuous Integration (CI) enforces quality gates on every code check-in. The pipeline compiles the source, runs linters, executes unit/integration tests, checks for security vulnerabilities (SCA/SAST), and outputs built artifacts ready for deployment if all checks pass."},
                            {"type": "code", "language": "yaml", "value": "# GitHub Actions CI Workflow\nname: Test & Lint\non: [push, pull_request]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v3\n    - name: Set up Python\n      uses: actions/setup-python@v4\n      with:\n        python-version: '3.11'\n    - name: Run Tests\n      run: |\n        pip install pytest flake8\n        flake8 .\n        pytest"},
                            {"type": "callout", "kind": "tip", "title": "Fast Pipelines", "value": "Optimizing pipeline speed is a core DevOps duty. Use dependency caching (e.g. caching node_modules or pip downloads) and run test suites in parallel to keep developers productive."},
                            {"type": "knowledge_check", "question": "What is the primary goal of Continuous Integration (CI)?", "options": [
                                "To automatically deploy code straight to production without human review.",
                                "To integrate and test changes frequently to catch integration bugs early.",
                                "To write tests automatically."
                            ], "correct_index": 1, "explanation": "CI aims to integrate developer modifications frequently and run automated tests to find integration defects early."}
                        ]
                    }
                ]
            },
            {
                "slug": "cloud-devops-cloud-platforms",
                "title": "Cloud Compute, Storage & IAM",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Compute Models & Storage Options",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Virtual Servers vs Serverless vs Container Instances"},
                            {"type": "text", "value": "Cloud platforms provide multiple execution structures:\n- **IaaS (Virtual Machines)**: Full control over the server (AWS EC2, Compute Engine). High maintenance, manual scaling.\n- **Container Services**: Managed orchestrators (AWS ECS, Google Cloud Run). Scalable, handles OS patches.\n- **FaaS (Serverless Functions)**: Execute code on-demand (AWS Lambda, Cloud Functions). Scale-to-zero, event-driven, limited runtime execution duration."},
                            {"type": "callout", "kind": "important", "title": "Storage Paradigms", "value": "Match storage to application access patterns: **Object Storage** (AWS S3) for assets/blobs, **Block Storage** (AWS EBS) for virtual hard disks, and **Managed Databases** (AWS RDS) for relational datasets."},
                            {"type": "knowledge_check", "question": "Which service model is best suited for an event-driven, scale-to-zero thumbnail resize handler?", "options": [
                                "Infrastructure as a Service (IaaS)",
                                "Function as a Service (FaaS / Serverless)",
                                "Platform as a Service (PaaS)"
                            ], "correct_index": 1, "explanation": "FaaS/Serverless is ideal for short-lived, event-driven tasks because it triggers quickly, scales automatically, and scale-to-zero when idle."}
                        ]
                    }
                ]
            },
            {
                "slug": "cloud-devops-observability",
                "title": "Observability & Reliability",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "The Three Pillars: Metrics, Logs & Traces",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Diagnosing Production Systems"},
                            {"type": "text", "value": "Observability measures the internal state of a system based on its external outputs. The three pillars are:\n- **Metrics**: Numerical data representing system states over time (CPU load, request count, latency). Good for alerting.\n- **Logs**: Text records of events (with trace contexts). Good for debugging specific error occurrences.\n- **Traces**: End-to-end paths of single requests across multiple microservices. Good for isolating slow operations in distributed networks."},
                            {"type": "callout", "kind": "important", "title": "The Golden Signals", "value": "SRE teams monitor four core metrics: **Latency** (time taken to serve requests), **Traffic** (demand/requests per second), **Errors** (rate of failing requests), and **Saturation** (fraction of system resources utilized)."},
                            {"type": "knowledge_check", "question": "Which pillar is best for tracking a request across 10 microservices to find a bottleneck?", "options": [
                                "Metrics",
                                "Logs",
                                "Traces"
                            ], "correct_index": 2, "explanation": "Distributed tracing tracks request spans across boundaries, allowing you to see the exact time spent in each service path."}
                        ]
                    }
                ]
            }
        ]
    },
    "cybersecurity": {
        "title": "Cybersecurity Fundamentals",
        "description": "Defensive security, secure software design, web risks, and incident-ready engineering practices.",
        "topics": [
            {
                "slug": "cybersecurity-security-basics",
                "title": "Security Principles & Threat Modeling",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "The CIA Triad & Threat Modeling Frameworks",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Core Security Principles"},
                            {"type": "text", "value": "The foundation of information security is the **CIA Triad**:\n- **Confidentiality**: Ensuring data is accessible only to authorized entities (implemented via Encryption, Access Controls).\n- **Integrity**: Guaranteeing data has not been altered or tampered with (implemented via Hashing, Digital Signatures, Version Control).\n- **Availability**: Ensuring systems and data are accessible when needed (implemented via Redundancy, Load Balancing, DDoS Mitigation)."},
                            {"type": "callout", "kind": "info", "title": "STRIDE Threat Modeling", "value": "STRIDE stands for: **S**poofing, **T**ampering, **R**epudiation, **I**nformation Disclosure, **D**enial of Service, and **E**levation of Privilege. Developers use STRIDE to evaluate code boundaries and design systems securely."},
                            {"type": "knowledge_check", "question": "Which element of the CIA Triad does data encryption directly protect?", "options": [
                                "Integrity",
                                "Confidentiality",
                                "Availability"
                            ], "correct_index": 1, "explanation": "Encryption converts plaintext to ciphertext, preventing unauthorized parties from reading data and protecting confidentiality."}
                        ]
                    }
                ]
            },
            {
                "slug": "cybersecurity-identity-access",
                "title": "Identity, Authentication & Authorization",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Authentication vs. Authorization",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Securing System Access"},
                            {"type": "text", "value": "A critical distinction in identity security:\n- **Authentication (AuthN)**: Verifying who you are (e.g., username/password validation, MFA, SSH keys).\n- **Authorization (AuthC)**: Verifying what you are allowed to do (e.g., RBAC/Role-Based Access Control, ABAC/Attribute-Based Access Control). Access check permissions must occur server-side, not hidden in the frontend UI."},
                            {"type": "code", "language": "python", "value": "# Secure password hashing using bcrypt\nimport bcrypt\n\npassword = b'supersecret123'\nsalt = bcrypt.gensalt(rounds=12)\nhashed = bcrypt.hashpw(password, salt)\n\n# Verification\nprint(bcrypt.checkpw(password, hashed))  # True"},
                            {"type": "callout", "kind": "important", "title": "Password Hashing", "value": "Never store passwords in plaintext or MD5/SHA-256. Use slow, key-derivation algorithms like `bcrypt`, `Argon2`, or `PBKDF2` to protect hashes from offline GPU brute-force attacks."},
                            {"type": "knowledge_check", "question": "What is the difference between Authentication and Authorization?", "options": [
                                "Authentication checks permissions; Authorization verifies identity.",
                                "Authentication verifies identity; Authorization checks permissions/access rights.",
                                "They are synonyms."
                              ], "correct_index": 1, "explanation": "Authentication validates identity credentials, while Authorization controls access to resource operations."}
                        ]
                    }
                ]
            },
            {
                "slug": "cybersecurity-web-security",
                "title": "Web Application Security",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "OWASP Top 10: XSS, CSRF & SQL Injection",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Preventing Web Vulnerabilities"},
                            {"type": "text", "value": "Web application security focuses on protecting web entrypoints:\n- **SQL Injection (SQLi)**: Triggered by concatenating user inputs into database queries. Mitigated via Parameterized Queries / Prepared Statements.\n- **XSS (Cross-Site Scripting)**: Triggered by displaying unsanitized user inputs in HTML templates. Mitigated via Contextual Output Encoding.\n- **CSRF (Cross-Site Request Forgery)**: Trick a user's browser into executing unauthorized commands. Mitigated via Anti-CSRF Tokens and SameSite cookies."},
                            {"type": "code", "language": "python", "value": "# VULNERABLE to SQL Injection\n# db.execute(f\"SELECT * FROM users WHERE username = '{user_input}'\")\n\n# SECURE using parameterized query\ndb.execute(\"SELECT * FROM users WHERE username = %s\", (user_input,))"},
                            {"type": "callout", "kind": "important", "title": "Trust Boundaries", "value": "Treat all client-supplied data (HTTP headers, query variables, request body) as untrusted. Validate, sanitize, and encode inputs at the trust boundary."},
                            {"type": "knowledge_check", "question": "How do prepared statements prevent SQL Injection?", "options": [
                                "By encrypting database connection transactions.",
                                "By treating user input strictly as data parameters, preventing the database engine from executing input strings as SQL commands.",
                                "By blacklisting select special characters."
                            ], "correct_index": 1, "explanation": "Prepared statements send SQL structures and variables separately, ensuring the DB compiler parses variables strictly as values."}
                        ]
                    }
                ]
            },
            {
                "slug": "cybersecurity-network-crypto",
                "title": "Network Security & Applied Cryptography",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Symmetric vs. Asymmetric Cryptography & TLS",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Securing Data in Transit & Rest"},
                            {"type": "text", "value": "Applied cryptography is split into two primary architectures:\n- **Symmetric Cryptography**: Uses the same key for encryption and decryption (e.g. AES). Fast, used for bulk data encryption.\n- **Asymmetric Cryptography**: Uses a Public Key to encrypt and Private Key to decrypt (e.g. RSA, Elliptic Curves). Slow, used for identity verification and secure key exchange over insecure channels.\n- **TLS (Transport Layer Security)**: Combines both. Asymmetric crypto completes the handshake and authenticates certificates, establishing a temporary symmetric session key for fast transmission."},
                            {"type": "callout", "kind": "info", "title": "Hashing vs Encryption", "value": "Hashing is a **one-way** mathematical function that creates a fixed-size signature (cannot be decrypted). Encryption is a **two-way** function that can be reversed using the correct key."},
                            {"type": "knowledge_check", "question": "Which cryptographic method is used to encrypt bulk payload data during an active TLS session?", "options": [
                                "Asymmetric Encryption (RSA)",
                                "Symmetric Encryption (AES)",
                                "One-way Hashing (SHA-256)"
                            ], "correct_index": 1, "explanation": "Symmetric encryption is highly performant, which makes it perfect for bulk payload transfers once identity is verified using asymmetric keys during handshakes."}
                        ]
                    }
                ]
            },
            {
                "slug": "cybersecurity-incident-response",
                "title": "Security Monitoring & Incident Response",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Security Operations & Containment",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Managing Incidents"},
                            {"type": "text", "value": "Incident response follows a structured lifecycle: Preparation, Detection & Analysis, Containment, Eradication, Recovery, and Post-Incident Review. In modern organizations, Security Information and Event Management (SIEM) systems aggregate audit trails to isolate compromised endpoints."},
                            {"type": "callout", "kind": "important", "title": "Security Auditing Logs", "value": "Logs must protect integrity and confidentiality. Ensure that logs are shipped to read-only target servers and do not record sensitive information (like user passwords or full credit card numbers)."},
                            {"type": "knowledge_check", "question": "What is the primary action during the Containment phase of incident response?", "options": [
                                "Fix the code bug to prevent future attacks.",
                                "Isolate compromised systems to prevent the attack from spreading across the network.",
                                "Dumping the entire database for audit reviews."
                            ], "correct_index": 1, "explanation": "Containment limits the damage of the active security breach by isolating affected endpoints immediately."}
                        ]
                    }
                ]
            }
        ]
    },
    "data-analytics": {
        "title": "Data Analytics & Business Intelligence",
        "description": "Turn raw data into trustworthy analysis, dashboards, experiments, and decisions.",
        "topics": [
            {
                "slug": "data-analytics-analytics-sql",
                "title": "Analytical SQL & Data Modeling",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Window Functions & Analytical SQL",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Window Functions vs Group By"},
                            {"type": "text", "value": "Standard aggregation (`GROUP BY`) collapses individual rows into a single summary row. **Window Functions** perform calculations across a partition of rows related to the current row, but preserve the identity of individual rows. This is essential for cohort calculations, run-rates, and trends."},
                            {"type": "code", "language": "sql", "value": "-- Compute running total of sales partition by year\nSELECT \n    sale_date, \n    amount, \n    SUM(amount) OVER (PARTITION BY EXTRACT(YEAR FROM sale_date) ORDER BY sale_date) as running_total\nFROM sales;"},
                            {"type": "callout", "kind": "tip", "title": "Window Syntax", "value": "The `OVER` clause defines the 'window'. Inside `OVER`, `PARTITION BY` acts like group-by, and `ORDER BY` defines the sequence of cumulative operations."},
                            {"type": "knowledge_check", "question": "What is the key difference between GROUP BY and a window function?", "options": [
                                "Window functions are faster.",
                                "GROUP BY collapses rows, while window functions allow individual rows to retain their identities.",
                                "Window functions only work in Postgres."
                            ], "correct_index": 1, "explanation": "Window functions return a value for each row in the query, preserving the original dataset details while appending partition calculations."}
                        ]
                    }
                ]
            },
            {
                "slug": "data-analytics-statistics-experiments",
                "title": "Statistics & Experimentation",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "A/B Testing & Hypothesis Testing",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Designing Statistical Experiments"},
                            {"type": "text", "value": "Organizations use **A/B Testing** to compare a control group (A) against a variant (B) to verify if changes produce significant differences. To evaluate results:\n- **Null Hypothesis ($H_0$)**: No actual difference between versions.\n- **P-Value**: The probability of observing results as extreme as the current data assuming $H_0$ is true. If $p < 0.05$, we reject the null hypothesis, claiming statistical significance.\n- **Statistical Power**: The probability of correctly rejecting the null hypothesis when a true effect exists (usually targeted at 80%)."},
                            {"type": "callout", "kind": "warning", "title": "Peeking Pitfall", "value": "Repeatedly checking p-values during an active experiment and stopping early once it hits significance is called 'p-hacking' or 'peeking'. It increases the false positive rate drastically."},
                            {"type": "knowledge_check", "question": "What does a P-value of 0.01 imply in an A/B test?", "options": [
                                "There is a 1% chance the variant is better.",
                                "Assuming the null hypothesis is true, there is only a 1% chance of observing this difference by random noise.",
                                "The experiment has 1% statistical power."
                            ], "correct_index": 1, "explanation": "A lower p-value indicates that observing the data's difference by random chance is highly improbable, supporting statistical significance."}
                        ]
                    }
                ]
            },
            {
                "slug": "data-analytics-data-cleaning",
                "title": "Data Cleaning & Quality",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Data Imputation & Quality Validation",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Handling Dirty Datasets"},
                            {"type": "text", "value": "Dirty data degrades model quality. Analysts must clean datasets using systematic approaches:\n- **Missing Data**: Isolate if data is Missing Completely at Random (MCAR), Missing at Random (MAR), or Missing Not at Random (MNAR) before choosing median imputation vs model-based imputation.\n- **Duplicate De-duplication**: Differentiating transactional updates from duplicate database rows.\n- **Outliers**: Inspect outliers using Z-score or IQR thresholds before dropping them, as they could represent real anomalies."},
                            {"type": "code", "language": "python", "value": "# Drop duplicates and impute using pandas\nimport pandas as pd\n\ndf = pd.read_csv('raw_data.csv')\ndf_clean = df.drop_duplicates()\n\n# Impute missing values with median column value\nmedian_val = df_clean['salary'].median()\ndf_clean['salary'] = df_clean['salary'].fillna(median_val)"},
                            {"type": "callout", "kind": "info", "title": "Data Quality Contracts", "value": "Production data lines use schemas and tests (like Great Expectations or dbt validations) to verify input properties (non-nulls, unique columns) before loading them into pipelines."},
                            {"type": "knowledge_check", "question": "If outliers represent fraudulent transactions in credit card data, should you drop them?", "options": [
                                "Yes, because they skew distribution curves.",
                                "No, because in fraud detection, the outliers themselves are the target anomalies we want to identify.",
                                "Yes, standard procedure is always to drop outliers."
                            ], "correct_index": 1, "explanation": "In anomaly detection contexts (like fraud), outliers contain the primary data signal and must be preserved for modeling."}
                        ]
                    }
                ]
            },
            {
                "slug": "data-analytics-visualization-storytelling",
                "title": "Visualization & Data Storytelling",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Chart Selection & Design",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Designing Insightful Dashboards"},
                            {"type": "text", "value": "Effective visualization translates numbers into patterns. The chart choice depends on the question:\n- **Comparison**: Bar charts, line charts.\n- **Distribution**: Histograms, box plots (shows median, quartiles, outliers).\n- **Relationship**: Scatter plots.\n- **Composition**: Stacked bar charts (avoid pie charts for more than 3 categories)."},
                            {"type": "callout", "kind": "tip", "title": "Less is More", "value": "Minimize chart clutter. Remove non-functional grid lines, use color intentionally to draw eyes to key outliers or values, and ensure all labels are clear and accessible."},
                            {"type": "knowledge_check", "question": "Which chart type is best for showing the distribution of salary ranges and identifying outliers across different departments?", "options": [
                                "Pie Chart",
                                "Box Plot",
                                "Line Chart"
                            ], "correct_index": 1, "explanation": "A Box Plot displays the median, quartiles, and outliers clearly, making it the best choice for distribution analysis."}
                        ]
                    }
                ]
            },
            {
                "slug": "data-analytics-data-pipelines",
                "title": "Data Pipelines & Warehousing",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "ETL vs. ELT & Data Warehouses",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Modern Data Stack Architectures"},
                            {"type": "text", "value": "Data integration architectures have shifted:\n- **ETL (Extract, Transform, Load)**: Cleans and aggregates data in-memory before writing to target systems. Common for legacy architectures.\n- **ELT (Extract, Load, Transform)**: Loads raw data directly into powerful modern cloud data warehouses (Snowflake, BigQuery), then performs transformations inside the warehouse using SQL. This scales easily and simplifies data pipelines."},
                            {"type": "callout", "kind": "important", "title": "Batch vs Stream", "value": "Batch processing runs periodically (e.g. daily Cron jobs using Airflow). Stream processing runs continuously over live event streams (e.g. Apache Kafka, Flink) to serve near real-time dashboards."},
                            {"type": "knowledge_check", "question": "What is the primary benefit of the ELT approach over ETL in modern data stacks?", "options": [
                                "It uses less bandwidth.",
                                "It leverages the massive compute and storage capabilities of cloud data warehouses to transform data inside the target system.",
                                "It eliminates the extract phase entirely."
                            ], "correct_index": 1, "explanation": "ELT loads raw data quickly and performs transformations inside the destination data warehouse using SQL, simplifying engineering steps."}
                        ]
                    }
                ]
            }
        ]
    },
    "mobile-development": {
        "title": "Mobile Application Development",
        "description": "Engineer responsive, accessible, offline-aware mobile applications from UI to release.",
        "topics": [
            {
                "slug": "mobile-development-mobile-ui",
                "title": "Mobile UI, Accessibility & Navigation",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Declarative UI & Mobile Accessibility",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Modern Mobile Layouts"},
                            {"type": "text", "value": "Modern mobile frameworks (SwiftUI for iOS, Jetpack Compose for Android) have shifted from imperative XML/Storyboards to **declarative UI**. The UI is represented as a state machine: changes in state automatically trigger UI recomposition/re-rendering."},
                            {"type": "code", "language": "kotlin", "value": "// Jetpack Compose Declarative Counter example\n@Composable\ndef Counter() {\n    var count by remember { mutableStateOf(0) }\n    Button(onClick = { count++ }) {\n        Text(\"Clicked: $count times\")\n    }\n}"},
                            {"type": "callout", "kind": "important", "title": "Mobile Accessibility", "value": "Accessible apps require content labels for screen readers (VoiceOver/TalkBack), maintaining minimum touch target sizes of 48dp x 48dp, and supporting dynamic text resizing without clipping layout views."},
                            {"type": "knowledge_check", "question": "How does declarative UI handle screen updates compared to imperative UI?", "options": [
                                "By manually finding views (`findViewById`) and modifying attributes.",
                                "By treating the UI as a function of current state, automatically re-rendering when state variables change.",
                                "By refreshing the entire operating system screen."
                            ], "correct_index": 1, "explanation": "Declarative UI framework updates views automatically by re-evaluating composable functions when underlying state variables change."}
                        ]
                    }
                ]
            },
            {
                "slug": "mobile-development-mobile-architecture",
                "title": "Mobile Architecture & State",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "MVVM & State Management",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Model-View-ViewModel in Mobile"},
                            {"type": "text", "value": "The **MVVM** pattern is the standard architecture for mobile systems:\n- **Model**: Data source / business logic API.\n- **View**: Declarative layout layer that displays data and sends user events to ViewModel.\n- **ViewModel**: Manages UI state, exposes data flows (LiveData, StateFlow), and survives configuration shifts (like screen rotation). ViewModel should be free of direct framework imports to stay testable."},
                            {"type": "callout", "kind": "info", "title": "Dependency Injection", "value": "Mobile apps use DI frameworks (Hilt, Koin, Swinject) to inject network clients, repositories, and view models safely, preventing tight coupling and simplifying unit tests."},
                            {"type": "knowledge_check", "question": "Which component in MVVM is responsible for managing UI state and surviving configuration changes?", "options": [
                                "View",
                                "Model",
                                "ViewModel"
                            ], "correct_index": 2, "explanation": "The ViewModel holds and publishes UI states, surviving events like screen orientation changes in mobile lifecycles."}
                        ]
                    }
                ]
            },
            {
                "slug": "mobile-development-mobile-data",
                "title": "Networking, Storage & Offline Support",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Caching & Offline-First Strategy",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Synchronizing Local & Remote Data"},
                            {"type": "text", "value": "Mobile devices experience frequent network disconnects. **Offline-first** architecture uses a local database (SQLite/Room/CoreData) as the single source of truth for the UI. The app queries the local database and displays cached data immediately, while background threads fetch updates from the network and sync updates to the local database."},
                            {"type": "code", "language": "kotlin", "value": "// Network bound resource logic pattern\nfun getItems() = networkBoundResource(\n    query = { localDao.getAllItems() },\n    fetch = { networkApi.fetchLatestItems() },\n    saveFetchResult = { apiResult -> localDao.insertAll(apiResult) }\n)"},
                            {"type": "callout", "kind": "warning", "title": "Secure Local Storage", "value": "Never store sensitive tokens or user credentials in standard key-value storage (SharedPreferences/UserDefaults) in plaintext. Use secure variants (Android Keystore/EncryptedSharedPreferences, iOS Keychain)."},
                            {"type": "knowledge_check", "question": "What is the primary benefit of an offline-first architecture?", "options": [
                                "It reduces mobile battery consumption.",
                                "It ensures the app remains usable and displays cached data even when the device is completely offline.",
                                "It speeds up network download speeds."
                            ], "correct_index": 1, "explanation": "Offline-first apps display local cached data immediately, maintaining usability during network disruptions."}
                        ]
                    }
                ]
            },
            {
                "slug": "mobile-development-mobile-performance",
                "title": "Performance, Battery & Observability",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Optimizing Rendering & Battery",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Smooth UI and Power Management"},
                            {"type": "text", "value": "Mobile apps must maintain a target frame rate (usually 60fps or 120fps) to feel smooth. Slow rendering or long-running computations on the **Main Thread** cause the UI to stutter (jank) and can trigger Application Not Responding (ANR) errors. CPU-intensive or frequent network operations drain device battery quickly."},
                            {"type": "callout", "kind": "important", "title": "Offloading Work", "value": "Always move network calls, database queries, and complex calculations off the Main thread using thread management tools (Kotlin Coroutines, iOS Grand Central Dispatch)."},
                            {"type": "knowledge_check", "question": "What is the consequence of executing a heavy database query on the UI Main Thread?", "options": [
                                "The query executes faster.",
                                "The UI freezes, causing a stuttering user experience or triggering an ANR crash.",
                                "It automatically runs in the background."
                            ], "correct_index": 1, "explanation": "The main thread handles UI rendering. Blocking it halts screen refreshes, causing lag, stutters, or ANR crashes."}
                        ]
                    }
                ]
            },
            {
                "slug": "mobile-development-mobile-testing-release",
                "title": "Testing, Security & Release",
                "difficulty": "intermediate",
                "subtopics": [
                    {
                        "title": "Testing Frameworks & Store Release Tracks",
                        "content_blocks": [
                            {"type": "heading", "level": 2, "value": "Verifying and Shipping Apps"},
                            {"type": "text", "value": "Mobile test suites consist of:\n- **Unit Tests**: Verify ViewModel and Repository logic. Fast, runs on computer CPU.\n- **Instrumented / UI Tests**: Run on emulator or physical devices (Espresso, XCTest) to verify rendering, clicks, and page transitions.\n- **Release Pipeline**: Built apps are signed using developer keys, obfuscated (ProGuard/R8) to prevent reverse engineering, and shipped to store beta channels (Google Play Console internal tracks, TestFlight) before production rollout."},
                            {"type": "callout", "kind": "tip", "title": "Staged Rollout", "value": "Utilize staged rollouts (e.g. releasing to 5%, then 20%, then 100% of users) to monitor crash reports (Crashlytics) in production and stop releases if anomalies are detected."},
                            {"type": "knowledge_check", "question": "Why is code obfuscation (like ProGuard or R8) used in production builds?", "options": [
                                "To compile code to native assembly language.",
                                "To compress files and reduce download size.",
                                "To rename classes and methods to arbitrary names, making reverse engineering and security audits by attackers much more difficult."
                            ], "correct_index": 2, "explanation": "Obfuscation protects intellectual property and increases the effort needed to reverse engineer compiled APKs/IPAs."}
                        ]
                    }
                ]
            }
        ]
    }
}

async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]
    
    # 1. Update/Upsert the 4 domain cards in db.domains
    for slug, dom in DOMAINS.items():
        domain_card = {
            "slug": slug,
            "title": dom["title"],
            "description": dom["description"]
        }
        await db.domains.update_one({"slug": slug}, {"$set": domain_card}, upsert=True)
        print(f"Upserted domain card: {slug}")
        
        # 2. Clear out existing topics for this domain to avoid duplicates
        res = await db.topics.delete_many({"domain_slug": slug})
        print(f"Cleared {res.deleted_count} existing topics for domain '{slug}'.")
        
        # 3. Seed deep topics
        for topic in dom["topics"]:
            topic["domain_slug"] = slug  # ensure domain_slug is set
            await db.topics.update_one({"slug": topic["slug"]}, {"$set": topic}, upsert=True)
            print(f"  Upserted clean rich topic: {topic['slug']}")
            
    print("Successfully finished expanded domains seeding.")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
