import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

async def dedupe():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]

    pipeline = [
        {"$group": {"_id": "$slug", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    dupes = await db.topics.aggregate(pipeline).to_list(length=None)

    if not dupes:
        print("No duplicate slugs found.")
    for d in dupes:
        keep_id = d["ids"][0]
        remove_ids = d["ids"][1:]
        print(f"slug={d['_id']}: keeping {keep_id}, removing {remove_ids}")
        await db.topics.delete_many({"_id": {"$in": remove_ids}})

    print("Dedup complete.")
    client.close()

if __name__ == "__main__":
    asyncio.run(dedupe())