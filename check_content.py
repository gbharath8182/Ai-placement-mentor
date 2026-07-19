import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    async for doc in db.topics.find({}):
        print(f"[{doc.get('domain_slug')}] {doc.get('slug')} -- {doc.get('title')}")
        for sub in doc.get("subtopics", []):
            blocks = sub.get("content_blocks", [])
            print(f'    - {sub.get("title")}  ({len(blocks)} content blocks)')

asyncio.run(check())
