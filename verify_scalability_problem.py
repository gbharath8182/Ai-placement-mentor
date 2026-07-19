import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform
    count = await db.practice_problems.count_documents({"topic_slug": "scalability"})
    print("Practice problems for scalability:", count)

asyncio.run(main())
