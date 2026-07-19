import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform
    topic = await db.topics.find_one({"slug": "intro-ml"})
    subtopics = topic.get("subtopics", [])
    print(f"Subtopic count: {len(subtopics)}")
    for s in subtopics:
        print(f"  - {s['title']} [{s['difficulty']}]: {len(s['content_blocks'])} content_blocks")

asyncio.run(main())
