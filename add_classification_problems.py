import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    problems = [
        {
            "topic_slug": "classification",
            "title": "Compute Logistic Regression Probability",
            "difficulty": "easy",
            "description": "Read one line from stdin containing three space-separated floats: b0, b1, and x. Compute the logistic regression probability p(X) = e^(b0 + b1*x) / (1 + e^(b0 + b1*x)). Print the result rounded to 3 decimal places.\n\nExample:\nInput:\n-1.5 0.8 2\nOutput:\n0.500",
            "starter_code": "import math\n\nb0, b1, x = map(float, input().split())\nz = b0 + b1 * x\np = math.exp(z) / (1 + math.exp(z))\nprint(round(p, 3))\n",
            "test_cases": [
                {"input": "-1.5 0.8 2", "expected_output": "0.525"},
                {"input": "0 0 5", "expected_output": "0.5"},
                {"input": "2 -1 2", "expected_output": "0.5"}
            ]
        },
        {
            "topic_slug": "classification",
            "title": "K-Nearest Neighbors Classifier",
            "difficulty": "medium",
            "description": "Read input from stdin in this format:\nLine 1: K (integer)\nLine 2: number of training points, n\nNext n lines: each has two floats (x, y coordinate) followed by a class label (integer), space-separated\nLast line: the test point, two floats (x, y coordinate)\n\nUsing Euclidean distance, find the K nearest training points to the test point and print the majority class label. Break ties by picking the smaller label.\n\nExample:\nInput:\n3\n4\n1 1 0\n2 2 0\n8 8 1\n9 9 1\n5 5\nOutput:\n0",
            "starter_code": "k = int(input())\nn = int(input())\npoints = []\nfor _ in range(n):\n    x, y, label = input().split()\n    points.append((float(x), float(y), int(label)))\ntx, ty = map(float, input().split())\n\ndistances = [((px - tx) ** 2 + (py - ty) ** 2) ** 0.5 for px, py, _ in points]\nranked = sorted(zip(distances, [p[2] for p in points]), key=lambda pair: pair[0])\nk_nearest_labels = [label for _, label in ranked[:k]]\n\ncounts = {}\nfor label in k_nearest_labels:\n    counts[label] = counts.get(label, 0) + 1\nmax_count = max(counts.values())\nwinners = sorted([label for label, c in counts.items() if c == max_count])\nprint(winners[0])\n",
            "test_cases": [
                {"input": "3\n4\n1 1 0\n2 2 0\n8 8 1\n9 9 1\n5 5", "expected_output": "0"},
                {"input": "1\n2\n0 0 0\n10 10 1\n1 1", "expected_output": "0"},
                {"input": "3\n3\n0 0 0\n0 1 1\n0 2 1\n0 1", "expected_output": "1"}
            ]
        }
    ]

    result = await db.practice_problems.insert_many(problems)
    print("Inserted IDs:", result.inserted_ids)

asyncio.run(main())
