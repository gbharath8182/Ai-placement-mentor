import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    problem = {
        "topic_slug": "cdn-content-delivery",
        "title": "Simulate TTL-Based Cache Expiry",
        "difficulty": "easy",
        "description": "Read input from stdin in this format:\nLine 1: number of events, n\nNext n lines: each is one of:\n  'SET key value ttl time' -- store key with the given value, set to expire at (time + ttl)\n  'GET key time' -- at the given time, print the value if key exists and has not expired (current time < expiry time), otherwise print 'MISS'\nAll times and ttl are integers.\n\nExample:\nInput:\n4\nSET a 100 10 0\nGET a 5\nGET a 15\nGET b 0\nOutput:\n100\nMISS\nMISS",
        "starter_code": "n = int(input())\nstore = {}\noutput = []\n\nfor _ in range(n):\n    parts = input().split()\n    if parts[0] == \"SET\":\n        key, value, ttl, time = parts[1], parts[2], int(parts[3]), int(parts[4])\n        store[key] = (value, time + ttl)\n    else:  # GET\n        key, time = parts[1], int(parts[2])\n        if key in store:\n            value, expiry = store[key]\n            if time < expiry:\n                output.append(value)\n            else:\n                output.append(\"MISS\")\n        else:\n            output.append(\"MISS\")\n\nprint(\"\\n\".join(output))\n",
        "test_cases": [
            {"input": "4\nSET a 100 10 0\nGET a 5\nGET a 15\nGET b 0", "expected_output": "100\nMISS\nMISS"},
            {"input": "3\nSET x 42 5 10\nGET x 14\nGET x 15", "expected_output": "42\nMISS"},
            {"input": "2\nGET z 0\nSET z 7 100 0", "expected_output": "MISS"}
        ]
    }

    result = await db.practice_problems.insert_one(problem)
    print("Inserted practice problem with id:", result.inserted_id)

asyncio.run(main())
