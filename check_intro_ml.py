import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    topic = await db.topics.find_one({"slug": "intro-ml"})
    print(json.dumps(topic, indent=2, default=str))

asyncio.run(main())
