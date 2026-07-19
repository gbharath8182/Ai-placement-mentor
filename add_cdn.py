import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    topic = {
        "domain_slug": "system-design",
        "slug": "cdn-content-delivery",
        "title": "CDN & Content Delivery",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "What a CDN Solves",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Serving Static Content Close to the User"},
                    {"type": "text", "value": "A **Content Delivery Network (CDN)** is a network of geographically distributed servers ('edge servers' or 'points of presence') that cache static content -- images, videos, CSS, JavaScript -- closer to end users. Instead of every request traveling all the way to a single origin server, users are served from the nearest edge location."},
                    {"type": "list", "ordered": False, "items": [
                        "**Reduced latency**: content travels a shorter physical distance to reach the user",
                        "**Reduced origin load**: the origin server handles far fewer requests since most are served from edge caches",
                        "**Improved availability**: if the origin server is temporarily unreachable, some CDNs can still serve cached content"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "When a system design question mentions global users or heavy static asset traffic (images, video, downloads), mentioning a CDN early signals you're thinking about latency and origin load, not just the application's internal architecture."}
                ]
            },
            {
                "title": "Push CDNs vs. Pull CDNs",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Two Models for Getting Content Onto the CDN"},
                    {"type": "text", "value": "**Push CDN**: the origin server is responsible for uploading content directly to the CDN whenever it changes. This gives full control over what's cached and when, but requires the origin to actively manage uploads -- better suited for sites with a smaller, less frequently changing set of assets."},
                    {"type": "text", "value": "**Pull CDN**: the CDN fetches content from the origin **on-demand**, the first time it's requested, then caches it for a configured TTL (time-to-live). This requires far less management -- new content is picked up automatically -- but the very first request for any asset is a cache miss and hits the origin directly."},
                    {"type": "callout", "kind": "important", "title": "Choosing Between Them", "value": "Pull CDNs are the more common default for most web applications because they need minimal setup. Push CDNs are favored when traffic is relatively low/predictable, or when precise control over exactly what's cached (and when it's refreshed) matters more than convenience."},
                    {"type": "list", "ordered": False, "items": [
                        "Pull CDN: less origin management, but first request per asset is always slow (cache miss)",
                        "Push CDN: origin must actively push updates, but every cached asset is guaranteed fresh from the moment it's pushed",
                        "Most large-scale sites with frequently changing content favor pull CDNs with sensible TTLs"
                    ]}
                ]
            },
            {
                "title": "Cache Control & Invalidation on a CDN",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Controlling Freshness With HTTP Headers"},
                    {"type": "text", "value": "CDNs (and browsers) respect the standard `Cache-Control` HTTP header to decide how long to keep an asset before re-checking with the origin."},
                    {"type": "code", "language": "text", "value": "Cache-Control: max-age=86400, public\n# max-age: how many seconds the response can be cached\n# public: can be cached by shared caches (CDN nodes), not just the browser"},
                    {"type": "list", "ordered": False, "items": [
                        "`max-age`: number of seconds the asset is considered fresh",
                        "`public` / `private`: whether shared caches (CDNs) can cache it, or only the end user's browser",
                        "`no-cache`: the cache must revalidate with the origin before using a cached copy (doesn't mean 'don't cache')",
                        "`no-store`: the response must never be cached at all -- appropriate for sensitive, user-specific data"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "Interview Trap: no-cache vs. no-store", "value": "`no-cache` does NOT mean 'do not cache' -- it means the cache can store the response but must revalidate with the origin before serving it. `no-store` is the directive that means 'never cache this at all.' Mixing these up is a common and noticeable interview mistake."},
                    {"type": "text", "value": "Once content changes before its TTL expires, the origin can force an update via **cache invalidation** -- either by explicitly purging the CDN's cached copy via an API call, or more simply, by changing the asset's URL (e.g. appending a version hash like `style.a1b2c3.css`) so the CDN treats it as an entirely new, uncached resource."},
                    {"type": "divider"},
                    {"type": "text", "value": "Versioned filenames are the more common approach in practice -- they sidestep invalidation entirely by making stale content simply unreachable under the old URL, and they work identically whether the underlying cache is a CDN, a browser, or an intermediate proxy."}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print("Inserted topic with id:", result.inserted_id)

asyncio.run(main())
