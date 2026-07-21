import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    old_desc = "Read two lines from stdin. The first line contains space-separated true values (y_true). The second line contains space-separated predicted values (y_pred), same length as the first. Print the Mean Squared Error, rounded to 2 decimal places.\n\nExample:\nInput:\n3 5 2 7\n2.5 5 4 8\nOutput:\n0.94"
    new_desc = old_desc.replace("Output:\n0.94", "Output:\n1.31")

    result = await db.practice_problems.update_one(
        {"topic_slug": "intro-ml", "title": "Compute Mean Squared Error"},
        {"$set": {"description": new_desc}}
    )
    print("Matched:", result.matched_count, "Modified:", result.modified_count)

asyncio.run(main())
