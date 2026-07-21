"""Seed dense, dashboard-visible learning paths for additional placement domains."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

DOMAINS = {
    "cloud-devops": {
        "title": "Cloud, DevOps & SRE",
        "description": "Build, ship, observe, and operate reliable software in modern cloud environments.",
        "reference": ("Google SRE Book", "https://sre.google/sre-book/table-of-contents/"),
        "topics": [
            ("linux-networking", "Linux, Networking & Shell", "Processes, permissions, files, sockets, DNS, and command-line diagnosis for production environments."),
            ("containers", "Containers & Docker", "Images, layers, registries, volumes, networking, and repeatable local environments."),
            ("cicd", "CI/CD & Release Engineering", "Pipelines, quality gates, artifacts, feature flags, rollbacks, and deployment strategies."),
            ("cloud-platforms", "Cloud Compute, Storage & IAM", "Compute choices, object storage, managed databases, networks, and least-privilege identity."),
            ("observability", "Observability & Reliability", "Metrics, logs, traces, SLOs, alerts, capacity planning, and incident response."),
        ],
    },
    "cybersecurity": {
        "title": "Cybersecurity Fundamentals",
        "description": "Defensive security, secure software design, web risks, and incident-ready engineering practices.",
        "reference": ("OWASP Web Security Testing Guide", "https://owasp.org/www-project-web-security-testing-guide/"),
        "topics": [
            ("security-basics", "Security Principles & Threat Modeling", "Assets, adversaries, attack surfaces, trust boundaries, risk, and practical threat models."),
            ("identity-access", "Identity, Authentication & Authorization", "Passwords, MFA, sessions, tokens, RBAC, ABAC, and secure permission checks."),
            ("web-security", "Web Application Security", "Injection, XSS, CSRF, SSRF, secure headers, validation, and safe output handling."),
            ("network-crypto", "Network Security & Applied Cryptography", "TLS, certificates, hashes, symmetric and asymmetric encryption, and key management."),
            ("incident-response", "Security Monitoring & Incident Response", "Logging, detection, containment, recovery, post-incident learning, and responsible disclosure."),
        ],
    },
    "data-analytics": {
        "title": "Data Analytics & Business Intelligence",
        "description": "Turn raw data into trustworthy analysis, dashboards, experiments, and decisions.",
        "reference": ("Python Data Science Handbook", "https://jakevdp.github.io/PythonDataScienceHandbook/"),
        "topics": [
            ("analytics-sql", "Analytical SQL & Data Modeling", "Joins, aggregations, windows, dimensional models, metrics definitions, and query reliability."),
            ("statistics-experiments", "Statistics & Experimentation", "Distributions, confidence intervals, hypothesis tests, A/B testing, bias, and causality limits."),
            ("data-cleaning", "Data Cleaning & Quality", "Missing values, duplicates, outliers, data contracts, validation, and reproducible transformations."),
            ("visualization-storytelling", "Visualization & Data Storytelling", "Chart selection, accessible design, uncertainty, dashboard hierarchy, and decision-focused narratives."),
            ("data-pipelines", "Data Pipelines & Warehousing", "Batch versus streaming, ELT, orchestration, lineage, warehouses, and cost-aware modeling."),
        ],
    },
    "mobile-development": {
        "title": "Mobile Application Development",
        "description": "Engineer responsive, accessible, offline-aware mobile applications from UI to release.",
        "reference": ("Android Developers Guide", "https://developer.android.com/guide"),
        "topics": [
            ("mobile-ui", "Mobile UI, Accessibility & Navigation", "Screen hierarchy, adaptive layouts, accessibility, gestures, navigation state, and design-system reuse."),
            ("mobile-architecture", "Mobile Architecture & State", "MVC/MVVM patterns, state ownership, dependency injection, lifecycle events, and modular boundaries."),
            ("mobile-data", "Networking, Storage & Offline Support", "API clients, caching, retries, local persistence, sync conflicts, and secure storage."),
            ("mobile-performance", "Performance, Battery & Observability", "Rendering, memory, startup time, battery cost, crash reporting, and field diagnostics."),
            ("mobile-testing-release", "Testing, Security & Release", "Unit/UI tests, signing, store release tracks, privacy, permissions, and rollback planning."),
        ],
    },
}


def subtopic(title, focus, reference, position):
    labels = ["Mental model", "Practical workflow", "Interview and project lens"]
    prompts = [
        f"Understand the purpose, vocabulary, and constraints behind {title.lower()}. {focus}",
        f"Apply {title.lower()} in a small project: define inputs, make failure paths explicit, test boundaries, and document trade-offs.",
        f"Explain {title.lower()} using a real scenario. State the decision, alternatives, risks, and how you would measure success.",
    ]
    return {
        "title": labels[position],
        "content_blocks": [
            {"type": "heading", "level": 2, "value": labels[position]},
            {"type": "text", "value": prompts[position]},
            {"type": "list", "items": ["Define the problem before selecting a tool.", "Identify one trade-off and one failure mode.", "Connect the concept to a measurable project outcome."], "ordered": False},
            {"type": "callout", "kind": "important", "title": "Placement signal", "value": "A strong answer connects fundamentals to reliability, user impact, and a concrete engineering choice."},
            {"type": "resource_link", "label": f"Reference: {reference[0]}", "url": reference[1]},
        ],
    }


async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]
    count = 0
    for slug, domain in DOMAINS.items():
        await db.domains.update_one({"slug": slug}, {"$set": {"slug": slug, "title": domain["title"], "description": domain["description"]}}, upsert=True)
        for suffix, title, focus in domain["topics"]:
            await db.topics.update_one(
                {"slug": f"{slug}-{suffix}"},
                {"$set": {"domain_slug": slug, "slug": f"{slug}-{suffix}", "title": title, "difficulty": "intermediate", "subtopics": [subtopic(title, focus, domain["reference"], i) for i in range(3)]}},
                upsert=True,
            )
            count += 1
    print(f"Seeded {len(DOMAINS)} domains, {count} topics, and {count * 3} subtopics.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
