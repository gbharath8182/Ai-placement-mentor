import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    topic = {
        "domain_slug": "system-design",
        "slug": "load-balancing-consistent-hashing",
        "title": "Load Balancing & Consistent Hashing",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Load Balancing Algorithms",
                "difficulty": "beginner",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "How a Load Balancer Picks a Server"},
                    {"type": "text", "value": "A load balancer needs an algorithm to decide which server in the pool receives each incoming request. The right choice depends on the workload."},
                    {"type": "list", "ordered": False, "items": [
                        "**Round robin**: requests are distributed to servers in rotating order. Simple, but ignores each server's actual current load.",
                        "**Least connections**: routes to whichever server currently has the fewest active connections. Better for workloads where requests take variable amounts of time.",
                        "**Weighted round robin / least connections**: same idea, but accounts for servers having different capacities (e.g. a bigger server gets proportionally more traffic).",
                        "**IP hash**: hashes the client's IP to consistently route the same client to the same server -- useful for session affinity ('sticky sessions')."
                    ]},
                    {"type": "callout", "kind": "tip", "title": "Interview Framing", "value": "Round robin is the easy default answer, but naming least-connections or IP-hash and explaining *when* they're better (uneven request duration, session stickiness) shows deeper understanding than reciting round robin alone."},
                    {"type": "text", "value": "Load balancers also operate at different layers: **Layer 4 (transport)** load balancers route based on IP and port without inspecting request content, offering high speed. **Layer 7 (application)** load balancers can inspect HTTP headers, cookies, and URLs, enabling smarter routing at the cost of more overhead."}
                ]
            },
            {
                "title": "The Problem With Naive Hashing",
                "difficulty": "intermediate",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Why hash(key) % N Breaks Down"},
                    {"type": "text", "value": "A common way to decide which of N servers should own a given key is `server_index = hash(key) % N`. This works fine -- until a server is added or removed and N changes."},
                    {"type": "code", "language": "python", "value": "def naive_hash_assign(key, num_servers):\n    return hash(key) % num_servers"},
                    {"type": "callout", "kind": "warning", "title": "The Core Problem", "value": "When N changes (a server is added or removed), almost **every key's assignment changes**, because the modulo operation depends on the total count. This forces a massive, expensive remapping and cache/data migration across nearly the entire cluster -- for something as routine as adding one more server."},
                    {"type": "text", "value": "This is exactly the problem **consistent hashing** was designed to solve: minimize the number of keys that need to move when the number of servers changes."}
                ]
            },
            {
                "title": "Consistent Hashing",
                "difficulty": "advanced",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Hashing Servers and Keys Onto the Same Ring"},
                    {"type": "text", "value": "Consistent hashing maps both servers and keys onto the same conceptual **hash ring** (a circular hash space, e.g. 0 to 2^32-1). Each key is assigned to the first server encountered by moving clockwise around the ring from the key's hash position."},
                    {"type": "list", "ordered": True, "items": [
                        "Hash each server to one or more positions on the ring",
                        "Hash each key onto the same ring",
                        "For a given key, walk clockwise until you hit a server -- that server owns the key",
                        "When a server is added: it only takes over keys between itself and the next server counter-clockwise -- all other key assignments are untouched",
                        "When a server is removed: its keys are picked up by the next server clockwise -- again, only a small fraction of keys move"
                    ]},
                    {"type": "callout", "kind": "important", "title": "Virtual Nodes", "value": "Hashing each physical server to just one ring position can create uneven load if servers land unevenly around the ring, or if server capacities differ. The fix is **virtual nodes**: each physical server is hashed to many positions on the ring, smoothing out the distribution and making it easy to give a more powerful server proportionally more virtual nodes."},
                    {"type": "code", "language": "python", "value": "import bisect, hashlib\n\nclass ConsistentHashRing:\n    def __init__(self, virtual_nodes=3):\n        self.virtual_nodes = virtual_nodes\n        self.ring = {}\n        self.sorted_keys = []\n\n    def _hash(self, key):\n        return int(hashlib.md5(key.encode()).hexdigest(), 16)\n\n    def add_server(self, server):\n        for i in range(self.virtual_nodes):\n            h = self._hash(f\"{server}#{i}\")\n            self.ring[h] = server\n            bisect.insort(self.sorted_keys, h)\n\n    def get_server(self, key):\n        h = self._hash(key)\n        idx = bisect.bisect(self.sorted_keys, h) % len(self.sorted_keys)\n        return self.ring[self.sorted_keys[idx]]"},
                    {"type": "divider"},
                    {"type": "text", "value": "Consistent hashing is used widely in practice -- Amazon's DynamoDB, Apache Cassandra, and many CDN and load balancer implementations all rely on it to distribute data or requests while minimizing reshuffling as the cluster changes size."}
                ]
            }
        ]
    }

    result = await db.topics.insert_one(topic)
    print("Inserted topic with id:", result.inserted_id)

asyncio.run(main())
