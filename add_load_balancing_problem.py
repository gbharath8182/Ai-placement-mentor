import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    problem = {
        "topic_slug": "load-balancing-consistent-hashing",
        "title": "Consistent Hashing: Find the Owning Server",
        "difficulty": "medium",
        "description": "Read input from stdin in this format:\nLine 1: ring size M (positions range from 0 to M-1)\nLine 2: number of servers, S\nLine 3: S space-separated integers -- the ring positions of servers labeled 0, 1, ..., S-1 in the order given\nLine 4: number of keys, K\nLine 5: K space-separated integers -- the ring positions of the keys\n\nFor each key, find the server whose position is the first one reached going clockwise (i.e. the smallest server position that is >= the key's position; if none exists, wrap around to the server with the smallest position). Print the owning server's label for each key, one per line, in the order the keys were given.\n\nExample:\nInput:\n100\n3\n10 40 70\n3\n5 50 95\nOutput:\n0\n2\n0",
        "starter_code": "m = int(input())\ns = int(input())\nserver_positions = list(map(int, input().split()))\nk = int(input())\nkey_positions = list(map(int, input().split()))\n\n# Pair each position with its original label, then sort by position\nlabeled = sorted(range(s), key=lambda i: server_positions[i])\nsorted_positions = [server_positions[i] for i in labeled]\n\noutput = []\nfor key in key_positions:\n    owner_label = None\n    for idx, pos in enumerate(sorted_positions):\n        if pos >= key:\n            owner_label = labeled[idx]\n            break\n    if owner_label is None:\n        owner_label = labeled[0]  # wrap around to smallest position\n    output.append(str(owner_label))\n\nprint(\"\\n\".join(output))\n",
        "test_cases": [
            {"input": "100\n3\n10 40 70\n3\n5 50 95", "expected_output": "0\n2\n0"},
            {"input": "50\n2\n25 5\n2\n10 40", "expected_output": "0\n1"},
            {"input": "20\n1\n15\n3\n0 15 19", "expected_output": "0\n0\n0"}
        ]
    }

    result = await db.practice_problems.insert_one(problem)
    print("Inserted practice problem with id:", result.inserted_id)

asyncio.run(main())
