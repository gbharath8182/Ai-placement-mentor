import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    topic = await db.topics.find_one({"slug": "python-strings-regex"})
    subtopics = topic.get("subtopics", [])
    total_blocks = sum(len(st.get("content_blocks", [])) for st in subtopics)
    problems = await db.practice_problems.count_documents({"topic_slug": "python-strings-regex"})
    print(f"python-strings-regex: subtopics={len(subtopics)} blocks={total_blocks} problems={problems}")
    for st in subtopics:
        title = st['title']
        diff = st.get('difficulty')
        blocks = len(st.get('content_blocks', []))
        print(f"  - {title} [{diff}] ({blocks} blocks)")

asyncio.run(main())
