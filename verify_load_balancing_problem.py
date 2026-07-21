import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    count = await db.practice_problems.count_documents({"topic_slug": "load-balancing-consistent-hashing"})
    print("Practice problems:", count)

asyncio.run(main())
