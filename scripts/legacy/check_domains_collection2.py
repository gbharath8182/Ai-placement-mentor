import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    docs = await db.domains.find().to_list(length=None)
    print(f"domains collection count: {len(docs)}")
    for d in docs:
        print(json.dumps(d, indent=2, default=str))

asyncio.run(main())
