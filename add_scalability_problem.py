import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    problem = {
        "topic_slug": "scalability",
        "title": "Implement an LRU Cache",
        "difficulty": "medium",
        "description": "Read input from stdin in this format:\nLine 1: capacity (integer)\nLine 2: number of operations, n\nNext n lines: each is either 'PUT key value' or 'GET key' (space-separated, key and value are integers)\n\nImplement an LRU (Least Recently Used) cache with the given capacity. For each GET, print the value if the key exists, otherwise print -1. PUT should insert or update a key; if the cache is at capacity and a new key is inserted, evict the least recently used entry first. Both GET and PUT count as 'using' a key (moving it to most-recently-used).\n\nExample:\nInput:\n2\n4\nPUT 1 100\nPUT 2 200\nGET 1\nPUT 3 300\nOutput:\n100",
        "starter_code": "from collections import OrderedDict\n\ncapacity = int(input())\nn = int(input())\ncache = OrderedDict()\noutput = []\n\nfor _ in range(n):\n    parts = input().split()\n    if parts[0] == \"PUT\":\n        key, value = int(parts[1]), int(parts[2])\n        if key in cache:\n            cache.move_to_end(key)\n        cache[key] = value\n        if len(cache) > capacity:\n            cache.popitem(last=False)\n    else:  # GET\n        key = int(parts[1])\n        if key in cache:\n            cache.move_to_end(key)\n            output.append(str(cache[key]))\n        else:\n            output.append(\"-1\")\n\nprint(\"\\n\".join(output))\n",
        "test_cases": [
            {"input": "2\n4\nPUT 1 100\nPUT 2 200\nGET 1\nPUT 3 300", "expected_output": "100"},
            {"input": "2\n6\nPUT 1 10\nPUT 2 20\nPUT 3 30\nGET 1\nGET 2\nGET 3", "expected_output": "-1\n20\n30"},
            {"input": "1\n3\nPUT 1 5\nGET 1\nGET 2", "expected_output": "5\n-1"}
        ]
    }

    result = await db.practice_problems.insert_one(problem)
    print("Inserted practice problem with id:", result.inserted_id)

asyncio.run(main())
