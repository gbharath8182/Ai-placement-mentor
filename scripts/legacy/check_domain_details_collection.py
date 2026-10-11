import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    names = await db.list_collection_names()
    print("Collections:", names)
    if "domain_details" in names:
        count = await db.domain_details.count_documents({})
        print("domain_details doc count:", count)
        if count > 0:
            sample = await db.domain_details.find_one()
            print("Sample doc:", sample)

asyncio.run(main())
