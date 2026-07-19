import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    doc = await db.topics.find_one({"slug": "dsa-arrays"})
    for sub in doc.get("subtopics", []):
        print("===", sub.get("title"), "===")
        print(json.dumps(sub.get("content_blocks", []), indent=2))

asyncio.run(check())
