import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    topic = {
        "domain_slug": "system-design",
        "slug": "database-replication-sharding",
        "title": "Database Design, Replication & Sharding",
        "difficulty": "advanced",
        "subtopics": [
            {
                "title": "SQL vs. NoSQL",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Choosing a Database Model"},
                    {"type": "text", "value": "**Relational (SQL) databases** (PostgreSQL, MySQL) store data in structured tables with fixed schemas and enforce relationships via foreign keys. They provide strong consistency and support complex joins and transactions (ACID guarantees)."},
                    {"type": "text", "value": "**NoSQL databases** relax the fixed-schema and strong-consistency requirements in exchange for horizontal scalability and flexibility. Common categories: **key-value stores** (Redis, DynamoDB), **document stores** (MongoDB), **column-family stores** (Cassandra), and **graph databases** (Neo4j)."},
                    {"type": "list", "ordered": False, "items": [
                        "Choose SQL when data is highly relational, transactions matter, and schema is stable",
                        "Choose NoSQL when data is huge in scale, schema changes frequently, or the access pattern is simple key-based lookups",
                        "Many large systems use both -- SQL for core transactional data, NoSQL for high-throughput, loosely-structured data"
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "Never say 'NoSQL is more scalable so I'd always pick it.' Justify the choice using the actual access pattern and consistency needs described in the problem, not a blanket preference."}
                ]
            },
            {
                "title": "Database Replication",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Copying Data Across Multiple Servers"},
                    {"type": "text", "value": "**Replication** keeps copies of the same data on multiple database servers, improving both availability (if one server fails, others still serve data) and read throughput (reads can be spread across replicas)."},
                    {"type": "text", "value": "The most common pattern is **primary-replica (master-slave) replication**: all writes go to a single primary server, which then propagates changes to one or more replica servers. Replicas typically serve read traffic only."},
                    {"type": "list", "ordered": False, "items": [
                        "**Synchronous replication**: the primary waits for replicas to confirm the write before acknowledging it -- strong consistency, higher write latency",
                        "**Asynchronous replication**: the primary acknowledges the write immediately and propagates to replicas afterward -- lower latency, but replicas can briefly serve stale data",
                        "If the primary fails, one replica must be promoted to primary -- this failover process needs careful handling to avoid data loss or split-brain (two servers both thinking they're primary)"
                    ]},
                    {"type": "callout", "kind": "warning", "title": "Interview Trap: Replication Lag", "value": "With asynchronous replication, a user who just wrote data might read from a replica that hasn't caught up yet, appearing to 'lose' their own write. This is why read-after-write consistency (e.g. routing a user's own reads to the primary shortly after they write) is a real design concern, not an edge case to hand-wave."}
                ]
            },
            {
                "title": "Database Sharding",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Splitting Data Across Multiple Databases"},
                    {"type": "text", "value": "Replication solves read scaling and availability, but every replica still holds the **entire** dataset -- it doesn't help once the data itself is too large for one machine, or write throughput exceeds what a single primary can handle. **Sharding** solves this by splitting data into partitions ('shards'), each held on a separate database server."},
                    {"type": "text", "value": "A **sharding key** determines which shard a given row lives on (e.g. `user_id % num_shards`, or a hash of the key). Choosing a good sharding key is critical -- a poor choice creates a **hotspot**, where one shard receives disproportionate traffic while others sit idle."},
                    {"type": "code", "language": "python", "value": "def get_shard(user_id, num_shards):\n    return hash(user_id) % num_shards"},
                    {"type": "list", "ordered": False, "items": [
                        "**Hotspot risk**: sharding by signup date puts all of today's active users on one shard",
                        "**Joins across shards** become expensive or impossible -- queries that need data from multiple shards must be handled at the application layer",
                        "**Resharding** (changing the number of shards) is a major operation -- this is exactly the problem consistent hashing (covered in the Load Balancing topic) helps minimize"
                    ]},
                    {"type": "callout", "kind": "important", "title": "Sharding Is a Last Resort, Not a First Instinct", "value": "Sharding adds significant complexity -- cross-shard joins, transactions, and resharding are all hard problems. In interviews, justify sharding only after showing that vertical scaling, replication, and caching are insufficient for the given scale, rather than reaching for it immediately."},
                    {"type": "divider"},
                    {"type": "text", "value": "In practice, replication and sharding are combined: each shard is itself replicated for availability, giving both horizontal write scaling (via shards) and read scaling plus fault tolerance (via replicas within each shard)."}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print("Inserted topic with id:", result.inserted_id)

asyncio.run(main())
