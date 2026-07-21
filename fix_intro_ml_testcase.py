import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    result = await db.practice_problems.update_one(
        {"topic_slug": "intro-ml", "title": "Compute Mean Squared Error"},
        {"$set": {"test_cases.0.expected_output": "1.31"}}
    )
    print("Matched:", result.matched_count, "Modified:", result.modified_count)

    problem = await db.practice_problems.find_one({"topic_slug": "intro-ml", "title": "Compute Mean Squared Error"})
    print("Test cases now:", problem["test_cases"])

asyncio.run(main())
