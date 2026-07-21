import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    topic = await db.topics.find_one({"slug": "classification"})
    if not topic:
        print("NOT FOUND")
        return
    subtopics = topic.get("subtopics", [])
    print(f"Topic title: {topic['title']}, domain: {topic['domain_slug']}")
    print(f"Subtopic count: {len(subtopics)}")
    for s in subtopics:
        print(f"  - {s['title']} [{s['difficulty']}]: {len(s['content_blocks'])} content_blocks")

asyncio.run(main())
