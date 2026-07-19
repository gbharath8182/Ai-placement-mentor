import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    problems = [
        {
            "topic_slug": "linear-regression",
            "title": "Fit a Simple Linear Regression Line",
            "difficulty": "medium",
            "description": "Read two lines from stdin: the first is space-separated x values, the second is space-separated y values (same length). Compute the least-squares slope (b1) and intercept (b0). Print b0 and b1 space-separated, each rounded to 2 decimal places.\n\nExample:\nInput:\n1 2 3 4 5\n2 4 5 4 5\nOutput:\n2.20 0.60",
            "starter_code": "x = list(map(float, input().split()))\ny = list(map(float, input().split()))\n\nn = len(x)\nx_mean = sum(x) / n\ny_mean = sum(y) / n\n\nnumerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))\ndenominator = sum((x[i] - x_mean) ** 2 for i in range(n))\n\nb1 = numerator / denominator\nb0 = y_mean - b1 * x_mean\n\nprint(f\"{b0:.2f} {b1:.2f}\")\n",
            "test_cases": [
                {"input": "1 2 3 4 5\n2 4 5 4 5", "expected_output": "2.20 0.60"},
                {"input": "1 2 3\n1 2 3", "expected_output": "0.00 1.00"},
                {"input": "1 2 3 4\n3 3 3 3", "expected_output": "3.00 0.00"}
            ]
        },
        {
            "topic_slug": "linear-regression",
            "title": "Compute R-squared",
            "difficulty": "easy",
            "description": "Read two lines from stdin: the first is space-separated true values (y_true), the second is space-separated predicted values (y_pred), same length. Compute and print R-squared, rounded to 2 decimal places.\n\nExample:\nInput:\n3 5 7 9\n2.8 5.1 7.2 8.9\nOutput:\n0.99",
            "starter_code": "y_true = list(map(float, input().split()))\ny_pred = list(map(float, input().split()))\n\ny_mean = sum(y_true) / len(y_true)\nss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))\nss_tot = sum((yt - y_mean) ** 2 for yt in y_true)\n\nr2 = 1 - (ss_res / ss_tot)\nprint(round(r2, 2))\n",
            "test_cases": [
                {"input": "3 5 7 9\n2.8 5.1 7.2 8.9", "expected_output": "0.99"},
                {"input": "1 2 3 4\n1 2 3 4", "expected_output": "1.0"},
                {"input": "1 1 1 1\n2 0 2 0", "expected_output": "0.0"}
            ]
        }
    ]

    result = await db.practice_problems.insert_many(problems)
    print("Inserted IDs:", result.inserted_ids)

asyncio.run(main())
