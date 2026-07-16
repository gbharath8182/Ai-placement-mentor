import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

async def seed_database():
    print("Seeding database...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    
    # Extract DB name from URI
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0]
    if not db_name:
        db_name = "education_platform"
    db = client[db_name]
    
    # Clear existing data to ensure a fresh, clean demo
    await db.domains.delete_many({})
    await db.topics.delete_many({})
    await db.practice_problems.delete_many({})
    await db.user_progress.delete_many({})
    await db.chat_sessions.delete_many({})
    
    print("Cleared existing collections.")
    
    # 1. Seed Domains
    domains_data = [
        {
            "slug": "python",
            "title": "Python Programming",
            "description": "Master Python syntax, functional constructs, control flow, data structures, and scripting capabilities."
        },
        {
            "slug": "machine-learning",
            "title": "Machine Learning",
            "description": "Understand supervised and unsupervised models, training evaluation, regression, classification, and neural nets."
        },
        {
            "slug": "dsa",
            "title": "Data Structures & Algorithms",
            "description": "Deep dive into stacks, queues, trees, searching, sorting, hashing, and complexity analyses."
        }
    ]
    
    await db.domains.insert_many(domains_data)
    print("Seeded domains.")
    
    # 2. Seed Topics
    topics_data = [
        # PYTHON TOPICS
        {
            "domain_slug": "python",
            "slug": "intro-python",
            "title": "Introduction to Python",
            "content_blocks": [
                {
                    "type": "text", 
                    "value": "Python is a high-level, interpreted, general-purpose programming language. Created by Guido van Rossum and first released in 1991, Python's design philosophy emphasizes code readability with its notable use of significant whitespace."
                },
                {
                    "type": "text", 
                    "value": "Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects. Python is dynamically typed and garbage-collected."
                },
                {
                    "type": "code", 
                    "language": "python", 
                    "value": "# Basic print statement\nprint(\"Hello, Python!\")\n\n# Dynamic typing example\nx = 5\ny = \"Geeks\"\nprint(f\"{y} is {x} stars\")"
                },
                {
                    "type": "resource_link", 
                    "label": "Official Python Setup Guide", 
                    "url": "https://docs.python.org/3/using/index.html"
                },
                {
                    "type": "resource_link", 
                    "label": "Python Beginners Guide", 
                    "url": "https://www.python.org/about/gettingstarted/"
                }
            ],
            "difficulty": "beginner"
        },
        {
            "domain_slug": "python",
            "slug": "python-loops",
            "title": "Python Control Flow & Loops",
            "content_blocks": [
                {
                    "type": "text", 
                    "value": "Control flow in Python is governed by conditional statements (`if`, `elif`, `else`) and loops (`for`, `while`). Python uses indentation to define code blocks instead of curly braces."
                },
                {
                    "type": "text", 
                    "value": "The `for` loop in Python iterates over a sequence (such as a list, a tuple, a dictionary, a set, or a string) or other iterable objects. The `while` loop executes a block of code as long as a specified condition is true."
                },
                {
                    "type": "code", 
                    "language": "python", 
                    "value": "# Loop from 0 to 4\nfor i in range(5):\n    if i % 2 == 0:\n        print(f\"{i} is even\")\n    else:\n        print(f\"{i} is odd\")"
                },
                {
                    "type": "resource_link", 
                    "label": "Python Control Flow Reference Docs", 
                    "url": "https://docs.python.org/3/tutorial/controlflow.html"
                }
            ],
            "difficulty": "beginner"
        },
        {
            "domain_slug": "python",
            "slug": "python-collections",
            "title": "Python Collections & Structures",
            "content_blocks": [
                {
                    "type": "text", 
                    "value": "Python has four built-in collection types that organize multiple values:\n\n1. **List**: Ordered, mutable sequence of items. Declared using square brackets `[]`.\n2. **Tuple**: Ordered, immutable sequence of items. Declared using parentheses `()`.\n3. **Set**: Unordered, unindexed collection of unique elements. Declared using curly braces `{}`.\n4. **Dictionary**: Unordered, mutable collection of key-value pairs. Declared using curly braces with colons `{key: value}`."
                },
                {
                    "type": "code", 
                    "language": "python", 
                    "value": "# List operations\nlist_item = [1, 2, 3]\nlist_item.append(4)\n\n# Dictionary lookup\nstudent = {\"name\": \"Alex\", \"grade\": \"A\"}\nprint(student[\"name\"])"
                },
                {
                    "type": "resource_link", 
                    "label": "Python Data Structures Tutorial", 
                    "url": "https://docs.python.org/3/tutorial/datastructures.html"
                }
            ],
            "difficulty": "intermediate"
        },
        
        # MACHINE LEARNING TOPICS
        {
            "domain_slug": "machine-learning",
            "slug": "intro-ml",
            "title": "Introduction to Machine Learning",
            "content_blocks": [
                {
                    "type": "text", 
                    "value": "Machine Learning (ML) is a subset of artificial intelligence that empowers computers to learn and improve automatically from experience without being explicitly programmed."
                },
                {
                    "type": "text", 
                    "value": "It is divided primarily into three categories:\n- **Supervised Learning**: Training a model on labeled inputs (e.g., house price forecasting).\n- **Unsupervised Learning**: Discovering hidden patterns in unlabeled data (e.g., customer clustering).\n- **Reinforcement Learning**: Teaching an agent to maximize cumulative rewards through environmental trials."
                },
                {
                    "type": "code", 
                    "language": "python", 
                    "value": "import numpy as np\n# Sample dataset: X (features), Y (labels)\nX = np.array([[1], [2], [3], [4]])\ny = np.dot(X, [2]) + 3\nprint(\"Features X:\", X.tolist())\nprint(\"Labels y:\", y.tolist())"
                },
                {
                    "type": "resource_link", 
                    "label": "Scikit-Learn Official Site", 
                    "url": "https://scikit-learn.org/stable/"
                }
            ],
            "difficulty": "intermediate"
        },
        {
            "domain_slug": "machine-learning",
            "slug": "linear-regression",
            "title": "Linear Regression Basics",
            "content_blocks": [
                {
                    "type": "text", 
                    "value": "Linear regression is one of the simplest and most widely used supervised algorithms. It fits a straight line to modeling the relationship between an independent variable X and a dependent outcome Y."
                },
                {
                    "type": "text", 
                    "value": "The line equation is represented as:\n\n$$y = \\beta_0 + \\beta_1 X + \\epsilon$$\n\nwhere $\\beta_0$ is the intercept, $\\beta_1$ is the slope, and $\\epsilon$ represents random error. We minimize the Mean Squared Error (MSE) to find optimal parameters."
                },
                {
                    "type": "code", 
                    "language": "python", 
                    "value": "# Simple implementation using pure Python / math formula\ndef calculate_coefficients(x, y):\n    n = len(x)\n    mean_x, mean_y = sum(x)/n, sum(y)/n\n    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))\n    den = sum((x[i] - mean_x) ** 2 for i in range(n))\n    slope = num / den\n    intercept = mean_y - slope * mean_x\n    return intercept, slope\n\nintercept, slope = calculate_coefficients([1, 2, 3], [5, 7, 9])\nprint(f\"Fit Line: Y = {intercept} + {slope} * X\")"
                }
            ],
            "difficulty": "advanced"
        }
    ]
    
    await db.topics.insert_many(topics_data)
    print("Seeded topics.")
    
    # 3. Seed Practice Problems
    practice_data = [
        {
            "topic_slug": "intro-python",
            "title": "Hello World in Python",
            "difficulty": "easy",
            "description": "Write a Python script that outputs exactly 'Hello, World!' to stdout.",
            "starter_code": "# Complete the code\nprint(\"Hello, World!\")\n",
            "test_cases": [
                {
                    "input": "",
                    "expected_output": "Hello, World!"
                }
            ]
        },
        {
            "topic_slug": "python-loops",
            "title": "Sum of Evens Up to N",
            "difficulty": "easy",
            "description": "Write a program that reads an integer N from standard input (stdin) and prints the sum of all positive even integers up to N (inclusive).\n\nInput format: a single integer.\nOutput format: a single integer representing the sum.\n\nExample:\nInput: 6\nOutput: 12 (since 2 + 4 + 6 = 12)",
            "starter_code": "# Read integer N\nn = int(input())\n\n# Your logic below\nsum_evens = 0\nfor i in range(2, n + 1, 2):\n    sum_evens += i\nprint(sum_evens)\n",
            "test_cases": [
                {"input": "6", "expected_output": "12"},
                {"input": "10", "expected_output": "30"},
                {"input": "3", "expected_output": "2"}
            ]
        },
        {
            "topic_slug": "python-collections",
            "title": "Find Max and Min in a List",
            "difficulty": "medium",
            "description": "Read a sequence of space-separated integers from stdin. Output the minimum and maximum value found in the sequence, separated by a space.\n\nInput format: space-separated integers on a single line.\nOutput format: two integers: `min max`.\n\nExample:\nInput: 5 1 9 -2 4\nOutput: -2 9",
            "starter_code": "# Read list from stdin\nnumbers = list(map(int, input().split()))\n\n# Calculate min and max and print\nprint(f\"{min(numbers)} {max(numbers)}\")\n",
            "test_cases": [
                {"input": "5 1 9 -2 4", "expected_output": "-2 9"},
                {"input": "100 100 100", "expected_output": "100 100"},
                {"input": "-1 -5 -10 0 5", "expected_output": "-10 5"}
            ]
        }
    ]
    
    await db.practice_problems.insert_many(practice_data)
    print("Seeded practice problems.")
    print("Database seeding completed successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
