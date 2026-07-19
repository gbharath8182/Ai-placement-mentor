import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    new_subtopics = [
        {
            "title": "Scaling From Zero to Millions of Users",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "The Growth Story"},
                {"type": "text", "value": "System design interviews are usually framed as a growth story: how does an architecture evolve as user count goes from a handful to millions? Understanding this progression matters more than memorizing any single diagram."},
                {"type": "list", "ordered": True, "items": [
                    "**Single server**: web server, app, and database all on one machine -- fine for a prototype, breaks almost immediately under real traffic",
                    "**Separate database server**: split the database onto its own machine so web and data tiers can scale independently",
                    "**Add a load balancer + multiple web servers**: the web tier becomes horizontally scalable; the load balancer distributes incoming requests",
                    "**Add a cache**: most reads hit a small set of 'hot' data -- a cache in front of the database absorbs the bulk of read traffic",
                    "**Add a CDN**: static assets (images, JS, CSS) are served from edge locations near the user instead of the origin server",
                    "**Make the web tier stateless**: move session data out of individual web servers (e.g. into a shared cache or database) so any server can handle any request",
                    "**Database scaling**: replication for read-heavy scale, then sharding once a single database instance can no longer hold all the data",
                    "**Message queues**: decouple slow or bursty background work (e.g. video processing, sending emails) from the request path",
                    "**Multiple data centers, monitoring, and automation**: the final stages for true internet-scale, high-availability systems"
                ]},
                {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "When asked to design any large system, walking through this progression out loud -- rather than jumping straight to a complex final architecture -- shows the interviewer you understand *why* each component exists, not just that you memorized a diagram."},
                {"type": "resource_link", "label": "GitHub: The System Design Primer (Donne Martin)", "url": "https://github.com/donnemartin/system-design-primer"}
            ]
        },
        {
            "title": "Vertical vs. Horizontal Scaling & Load Balancers",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Two Ways to Handle More Load"},
                {"type": "text", "value": "**Vertical scaling (scale up)** means adding more resources -- CPU, RAM -- to a single existing server. **Horizontal scaling (scale out)** means adding more servers to a pool and distributing load across them."},
                {"type": "list", "ordered": False, "items": [
                    "Vertical scaling is simpler (no distributed-systems complexity) but has a hard ceiling -- there's a limit to how big a single machine can get, and it's a single point of failure",
                    "Horizontal scaling has effectively no ceiling and provides redundancy, but introduces real complexity: load balancing, data consistency across servers, and session management",
                    "Most large-scale systems favor horizontal scaling once they outgrow a single machine, accepting the added complexity in exchange for near-unlimited growth and fault tolerance"
                ]},
                {"type": "text", "value": "A **load balancer** sits between clients and the web servers, distributing incoming requests across the server pool. This solves two problems at once: it prevents any single server from being overwhelmed, and if one server goes down, the load balancer routes traffic to the remaining healthy servers, improving availability."},
                {"type": "callout", "kind": "important", "title": "Load Balancer Also Removes a Single Point of Failure -- Partially", "value": "A load balancer improves availability of the web tier, but it can itself become a single point of failure unless it's set up with a redundant secondary load balancer. This nuance is worth mentioning explicitly in interviews rather than treating the load balancer as an unconditional fix."},
                {"type": "divider"},
                {"type": "text", "value": "The mechanics of *how* a load balancer picks which server gets a request (round robin, least connections, consistent hashing, etc.) are covered in depth in the dedicated Load Balancing & Consistent Hashing topic."}
            ]
        },
        {
            "title": "Caching Fundamentals: Policies & Eviction",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Why and How to Cache"},
                {"type": "text", "value": "Caching stores copies of frequently-accessed ('hot') data in fast, temporary storage -- typically in-memory stores like Redis or Memcached -- so repeated requests can be served without hitting the slower primary database every time."},
                {"type": "heading", "level": 3, "value": "Caching Strategies"},
                {"type": "list", "ordered": False, "items": [
                    "**Cache-aside (lazy loading)**: the application checks the cache first; on a miss, it reads from the database and writes the result into the cache. Simple and widely used, but the first request for any given key is always a cache miss.",
                    "**Write-through**: writes go to the cache and the database at the same time, keeping the cache always consistent, at the cost of added write latency.",
                    "**Write-back (write-behind)**: writes go to the cache immediately and are asynchronously flushed to the database later -- fast writes, but risks data loss if the cache fails before flushing."
                ]},
                {"type": "code", "language": "python", "value": "def get_user(user_id, cache, db):\n    # Cache-aside pattern\n    cached = cache.get(user_id)\n    if cached is not None:\n        return cached  # cache hit\n    user = db.query_user(user_id)  # cache miss -> hit the DB\n    cache.set(user_id, user, ttl=300)  # populate cache for next time\n    return user"},
                {"type": "heading", "level": 3, "value": "Eviction and Expiration"},
                {"type": "text", "value": "Since cache memory is limited, an **eviction policy** decides what to remove when the cache is full. The most common is **LRU (Least Recently Used)** -- evict whatever hasn't been accessed in the longest time. A **TTL (Time To Live)** is also commonly set so stale data automatically expires even if it's still being accessed frequently."},
                {"type": "callout", "kind": "warning", "title": "Interview Trap: Cache Invalidation", "value": "Cache invalidation -- keeping cached data consistent with the source of truth after an update -- is famously one of the hardest problems in computer science. Don't wave it away; be ready to discuss TTLs, explicit invalidation on write, or accepting eventual consistency as deliberate tradeoffs."}
            ]
        }
    ]

    result = await db.topics.update_one(
        {"slug": "scalability"},
        {"$set": {"subtopics": new_subtopics}}
    )
    print("Matched:", result.matched_count, "Modified:", result.modified_count)

asyncio.run(main())
