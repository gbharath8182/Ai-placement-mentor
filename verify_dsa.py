import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    async for doc in db.topics.find({"domain_slug": "dsa"}):
        slug = doc.get("slug")
        subtopics = doc.get("subtopics", [])
        total_blocks = sum(len(s.get("content_blocks", [])) for s in subtopics)
        problem_count = await db.practice_problems.count_documents({"topic_slug": slug})
        print(f"{slug}: {len(subtopics)} subtopics, {total_blocks} total content blocks, {problem_count} practice problems")

asyncio.run(check())
