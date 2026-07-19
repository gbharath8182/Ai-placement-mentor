import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    topic = await db.topics.find_one({"slug": "python-strings-regex"})
    if topic:
        subtopics = topic.get("subtopics", [])
        print("=== SAMPLE SUBTOPIC (raw keys + one full example) ===")
        if subtopics:
            print("Keys present:", list(subtopics[0].keys()))
            print(json.dumps(subtopics[0], indent=2, default=str)[:1500])

    problem = await db.practice_problems.find_one({"topic_slug": "python-strings-regex"})
    print("\n=== SAMPLE PRACTICE PROBLEM (raw keys + full example) ===")
    if problem:
        print("Keys present:", list(problem.keys()))
        print(json.dumps(problem, indent=2, default=str))
    else:
        print("No practice problem found for that slug.")

asyncio.run(main())
