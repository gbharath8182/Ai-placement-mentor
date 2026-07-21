import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    problem = {
        "topic_slug": "intro-ml",
        "title": "Compute Mean Squared Error",
        "difficulty": "easy",
        "description": "Read two lines from stdin. The first line contains space-separated true values (y_true). The second line contains space-separated predicted values (y_pred), same length as the first. Print the Mean Squared Error, rounded to 2 decimal places.\n\nExample:\nInput:\n3 5 2 7\n2.5 5 4 8\nOutput:\n0.94",
        "starter_code": "y_true = list(map(float, input().split()))\ny_pred = list(map(float, input().split()))\n\nn = len(y_true)\nmse = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / n\nprint(round(mse, 2))\n",
        "test_cases": [
            {"input": "3 5 2 7\n2.5 5 4 8", "expected_output": "0.94"},
            {"input": "1 1 1\n1 1 1", "expected_output": "0.0"},
            {"input": "10 20\n12 18", "expected_output": "4.0"}
        ]
    }

    result = await db.practice_problems.insert_one(problem)
    print("Inserted practice problem with id:", result.inserted_id)

asyncio.run(main())
