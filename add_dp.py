import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-dynamic-programming",
    "title": "Dynamic Programming",
    "difficulty": "advanced",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Memoization vs Tabulation",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Avoiding Redundant Work"},
                {"type": "text", "value": "**Dynamic Programming** solves problems by breaking them into overlapping subproblems and storing (caching) each result so it's never recomputed. There are two equivalent ways to implement this: **memoization** (top-down -- write the natural recursive solution, then cache results in a dict/array) and **tabulation** (bottom-up -- build up an array of answers iteratively, starting from the smallest subproblems). The canonical example is Fibonacci: naive recursion is `O(2^n)` because it recomputes the same values exponentially many times; either DP approach brings it down to `O(n)`."},
                {"type": "list", "ordered": False, "items": [
                    "**Naive recursive Fibonacci** -- `O(2^n)` time, exponential blowup from recomputation",
                    "**Memoized (top-down)** -- `O(n)` time, `O(n)` space (cache + recursion stack)",
                    "**Tabulated (bottom-up)** -- `O(n)` time, `O(n)` space, but avoids recursion stack overhead/limits",
                    "**Space-optimized tabulation** -- for Fibonacci-like problems only needing the last 1-2 values, this drops to `O(1)` space"
                ]},
                {"type": "callout", "kind": "tip", "title": "The standard DP workflow", "value": "1) Write the brute-force recursive solution first, even if slow. 2) Identify the overlapping subproblems (same arguments called repeatedly). 3) Add memoization -- just a cache check at the top of the function. 4) If needed, convert to tabulation for better space/performance. Always start with step 1 -- don't try to jump straight to tabulation."},
                {"type": "code", "language": "python", "value": "# Naive -- O(2^n)\ndef fib_naive(n):\n    if n <= 1:\n        return n\n    return fib_naive(n-1) + fib_naive(n-2)\n\n# Memoized (top-down) -- O(n)\ndef fib_memo(n, cache=None):\n    if cache is None:\n        cache = {}\n    if n in cache:\n        return cache[n]\n    if n <= 1:\n        return n\n    cache[n] = fib_memo(n-1, cache) + fib_memo(n-2, cache)\n    return cache[n]\n\n# Tabulated (bottom-up) -- O(n) time, O(1) space\ndef fib_tab(n):\n    if n <= 1:\n        return n\n    prev2, prev1 = 0, 1\n    for _ in range(2, n + 1):\n        prev2, prev1 = prev1, prev1 + prev2\n    return prev1"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Dynamic Programming", "url": "https://www.geeksforgeeks.org/dynamic-programming/"}
            ]
        },
        {
            "title": "0/1 Knapsack",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Why Greedy Fails Here"},
                {"type": "text", "value": "Unlike Fractional Knapsack, **0/1 Knapsack** requires taking an item whole or not at all -- you can't split it. This breaks the greedy value-to-weight-ratio approach: a locally-best item can consume capacity that would've been better spent on two other items combined. The DP solution builds a 2D table `dp[i][w]` representing 'the best value achievable using the first `i` items with capacity `w`', filled bottom-up."},
                {"type": "list", "ordered": False, "items": [
                    "**Time complexity** -- `O(n * capacity)`, where n is the number of items",
                    "**Space complexity** -- `O(n * capacity)` for the full table, or `O(capacity)` with a rolling-array optimization",
                    "**Recurrence** -- `dp[i][w] = max(dp[i-1][w], dp[i-1][w-weight[i]] + value[i])` if the item fits, else just `dp[i-1][w]`"
                ]},
                {"type": "callout", "kind": "warning", "title": "Why greedy provably fails here", "value": "Consider items (value=60, weight=10), (value=100, weight=20), (value=120, weight=30) with capacity 50. Greedy-by-ratio takes item 1 and 2 for value 160, but the true optimum is items 2 and 3 for value 220 -- greedy's locally-best pick actively excludes the globally-best combination."},
                {"type": "code", "language": "python", "value": "def knapsack_01(values, weights, capacity):\n    n = len(values)\n    dp = [[0] * (capacity + 1) for _ in range(n + 1)]\n\n    for i in range(1, n + 1):\n        for w in range(capacity + 1):\n            if weights[i-1] <= w:\n                dp[i][w] = max(dp[i-1][w], dp[i-1][w - weights[i-1]] + values[i-1])\n            else:\n                dp[i][w] = dp[i-1][w]\n\n    return dp[n][capacity]\n\nvalues = [60, 100, 120]\nweights = [10, 20, 30]\nprint(knapsack_01(values, weights, 50))  # 220"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: 0/1 Knapsack Problem", "url": "https://www.geeksforgeeks.org/0-1-knapsack-problem-dp-10/"}
            ]
        },
        {
            "title": "Longest Common Subsequence",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Comparing Two Sequences"},
                {"type": "text", "value": "**Longest Common Subsequence (LCS)** finds the longest sequence that appears in both strings, in order but not necessarily contiguous (unlike a substring). This is the algorithm behind `diff` tools, version control merge logic, and DNA sequence comparison. Like Knapsack, it builds a 2D table: `dp[i][j]` = 'the LCS length using the first `i` characters of string A and the first `j` characters of string B'."},
                {"type": "list", "ordered": False, "items": [
                    "**Time complexity** -- `O(m * n)`, where m and n are the two string lengths",
                    "**Space complexity** -- `O(m * n)`, or `O(min(m, n))` with a rolling-array optimization since each row only depends on the previous row",
                    "**Recurrence** -- if characters match: `dp[i][j] = dp[i-1][j-1] + 1`; if not: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`"
                ]},
                {"type": "callout", "kind": "info", "title": "LCS vs Longest Common Substring", "value": "These are different problems that get confused often. LCS allows gaps ('ace' is a subsequence of 'abcde'); Longest Common **Substring** requires contiguous characters. The substring version has a similar but distinct DP recurrence -- it resets to 0 on any mismatch instead of taking a max."},
                {"type": "code", "language": "python", "value": "def lcs(a, b):\n    m, n = len(a), len(b)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n\n    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n            if a[i-1] == b[j-1]:\n                dp[i][j] = dp[i-1][j-1] + 1\n            else:\n                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n\n    return dp[m][n]\n\nprint(lcs(\"ABCBDAB\", \"BDCABA\"))  # 4 -- e.g. 'BCBA'"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Longest Common Subsequence", "url": "https://www.geeksforgeeks.org/longest-common-subsequence-dp-4/"}
            ]
        },
        {
            "title": "Matrix Chain Multiplication",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Optimizing Order of Operations"},
                {"type": "text", "value": "Matrix multiplication is associative -- `(AB)C` and `A(BC)` give the same result -- but the **number of scalar multiplications needed can differ enormously** depending on parenthesization. **Matrix Chain Multiplication** finds the optimal order to multiply a chain of matrices to minimize total operations. This is the classic **interval DP** pattern: `dp[i][j]` represents the minimum cost to multiply the matrices from index `i` to `j`, computed by trying every possible split point."},
                {"type": "list", "ordered": False, "items": [
                    "**Time complexity** -- `O(n^3)`, trying every split point for every interval",
                    "**Space complexity** -- `O(n^2)` for the DP table",
                    "**Interval DP pattern** -- this same 'try every split point in a range' structure also appears in Optimal Binary Search Tree and Burst Balloons problems"
                ]},
                {"type": "callout", "kind": "important", "title": "This is a different DP shape", "value": "Unlike Knapsack/LCS which fill a table left-to-right in a fairly linear order, interval DP fills by *increasing chain length* -- you need all shorter sub-chains solved before you can solve a longer one. Recognizing this shape (dp[i][j] over a range, split point search) is what separates 'knows Knapsack and LCS' from 'actually understands DP patterns.'"},
                {"type": "code", "language": "python", "value": "def matrix_chain_order(dims):\n    # dims: list where matrix i has dimensions dims[i-1] x dims[i]\n    n = len(dims) - 1  # number of matrices\n    dp = [[0] * n for _ in range(n)]\n\n    for length in range(2, n + 1):  # chain length\n        for i in range(n - length + 1):\n            j = i + length - 1\n            dp[i][j] = float('inf')\n            for k in range(i, j):\n                cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1]\n                dp[i][j] = min(dp[i][j], cost)\n\n    return dp[0][n-1]\n\n# Matrices of size 40x20, 20x30, 30x10, 10x30\ndims = [40, 20, 30, 10, 30]\nprint(matrix_chain_order(dims))  # 26000"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Matrix Chain Multiplication", "url": "https://www.geeksforgeeks.org/matrix-chain-multiplication-dp-8/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-dynamic-programming",
        "title": "0/1 Knapsack",
        "difficulty": "medium",
        "description": "Given n items with space-separated values on one line and weights on the next, and a capacity on the third line, print the maximum value achievable without splitting any item.",
        "starter_code": "def knapsack(values, weights, capacity):\n    n = len(values)\n    dp = [[0] * (capacity + 1) for _ in range(n + 1)]\n    for i in range(1, n + 1):\n        for w in range(capacity + 1):\n            if weights[i-1] <= w:\n                dp[i][w] = max(dp[i-1][w], dp[i-1][w - weights[i-1]] + values[i-1])\n            else:\n                dp[i][w] = dp[i-1][w]\n    return dp[n][capacity]\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nvalues = list(map(int, lines[0].split()))\nweights = list(map(int, lines[1].split()))\ncapacity = int(lines[2])\nprint(knapsack(values, weights, capacity))",
        "test_cases": [
            {"input": "60 100 120\n10 20 30\n50", "expected_output": "220"},
            {"input": "10\n5\n10", "expected_output": "10"},
            {"input": "10\n5\n4", "expected_output": "0"}
        ]
    },
    {
        "topic_slug": "dsa-dynamic-programming",
        "title": "Longest Common Subsequence Length",
        "difficulty": "medium",
        "description": "Given two strings on separate lines, print the length of their longest common subsequence.",
        "starter_code": "def lcs(a, b):\n    m, n = len(a), len(b)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n            if a[i-1] == b[j-1]:\n                dp[i][j] = dp[i-1][j-1] + 1\n            else:\n                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n    return dp[m][n]\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nprint(lcs(lines[0].strip(), lines[1].strip()))",
        "test_cases": [
            {"input": "ABCBDAB\nBDCABA", "expected_output": "4"},
            {"input": "abc\nabc", "expected_output": "3"},
            {"input": "abc\nxyz", "expected_output": "0"}
        ]
    },
    {
        "topic_slug": "dsa-dynamic-programming",
        "title": "Climbing Stairs (Memoization Warmup)",
        "difficulty": "easy",
        "description": "You can climb 1 or 2 steps at a time. Given n, print the number of distinct ways to reach the top.",
        "starter_code": "def climb_stairs(n, cache=None):\n    if cache is None:\n        cache = {}\n    if n in cache:\n        return cache[n]\n    if n <= 2:\n        return n\n    cache[n] = climb_stairs(n-1, cache) + climb_stairs(n-2, cache)\n    return cache[n]\n\nimport sys\nn = int(sys.stdin.readline())\nprint(climb_stairs(n))",
        "test_cases": [
            {"input": "2", "expected_output": "2"},
            {"input": "3", "expected_output": "3"},
            {"input": "5", "expected_output": "8"}
        ]
    }
]

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    existing = await db.topics.find_one({"slug": TOPIC["slug"]})
    if existing:
        print("SKIP -- topic already exists:", TOPIC["slug"])
    else:
        await db.topics.insert_one(TOPIC)
        print("Inserted topic:", TOPIC["slug"])

    for problem in PRACTICE_PROBLEMS:
        existing_p = await db.practice_problems.find_one({"topic_slug": problem["topic_slug"], "title": problem["title"]})
        if existing_p:
            print("SKIP -- problem already exists:", problem["title"])
        else:
            await db.practice_problems.insert_one(problem)
            print("Inserted problem:", problem["title"])

asyncio.run(main())
