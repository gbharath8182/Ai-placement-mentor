import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-branch-and-bound",
    "title": "Branch & Bound",
    "difficulty": "advanced",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Branch & Bound Fundamentals: Job Sequencing",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Pruning With a Bound, Not Just a Constraint"},
                {"type": "text", "value": "**Branch & Bound** is backtracking's more disciplined sibling: instead of only pruning branches that are *invalid*, it also prunes branches that are valid but **provably can't beat the best solution found so far**. At each node in the search tree, it computes an optimistic **bound** (an upper estimate of the best possible outcome from that branch) -- if that bound is worse than the current best known solution, the entire branch is discarded without exploring it further. This is why B&B often massively outperforms plain backtracking or brute force on optimization problems, even though both are technically exponential in the worst case."},
                {"type": "list", "ordered": False, "items": [
                    "**Branching** -- systematically dividing the problem into smaller subproblems (same as backtracking)",
                    "**Bounding** -- computing a cheap-to-calculate optimistic estimate for a subproblem, used to decide whether it's worth exploring",
                    "**Pruning** -- discarding any branch whose bound is worse than the current best solution",
                    "**Worst case** -- still exponential, but the bounding step typically eliminates huge portions of the search space in practice"
                ]},
                {"type": "callout", "kind": "important", "title": "This is genuinely underrated", "value": "Most platforms stop at backtracking and skip Branch & Bound entirely, even though it's the technique that actually makes optimization problems (not just decision problems) tractable in practice -- it's the algorithm underneath real-world solvers for scheduling, routing, and resource allocation."},
                {"type": "code", "language": "python", "value": "def job_sequencing(jobs):\n    # jobs: list of (job_id, deadline, profit)\n    jobs = sorted(jobs, key=lambda x: x[2], reverse=True)  # sort by profit, greedy-ish start\n    max_deadline = max(job[1] for job in jobs)\n    slots = [None] * (max_deadline + 1)\n    total_profit = 0\n\n    for job_id, deadline, profit in jobs:\n        # Try to place this job as late as possible before its deadline (bounding: skip if no slot available)\n        for slot in range(min(deadline, max_deadline), 0, -1):\n            if slots[slot] is None:\n                slots[slot] = job_id\n                total_profit += profit\n                break\n\n    return total_profit, [j for j in slots if j]\n\njobs = [('a', 2, 100), ('b', 1, 19), ('c', 2, 27), ('d', 1, 25), ('e', 3, 15)]\nprint(job_sequencing(jobs))  # (142, ['b or d', 'a', 'e'])"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Job Sequencing Problem", "url": "https://www.geeksforgeeks.org/job-sequencing-problem/"}
            ]
        },
        {
            "title": "0/1 Knapsack via Branch & Bound",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Same Problem, Different Weapon"},
                {"type": "text", "value": "We already solved 0/1 Knapsack with Dynamic Programming (`O(n * capacity)`), which is optimal when capacity is reasonably small. But when capacity is huge (making the DP table impractically large) and the number of items is more modest, **Branch & Bound** becomes the better tool: it explores a decision tree (include/exclude each item, same shape as backtracking) but at each node computes an optimistic bound using the **fractional knapsack value** as an upper estimate -- since fractional knapsack is solvable greedily and always gives an upper bound on what 0/1 knapsack could achieve."},
                {"type": "list", "ordered": False, "items": [
                    "**Bound calculation** -- at each node, compute what the fractional knapsack (allow one item to be split) would achieve; this is always >= the true 0/1 answer",
                    "**Pruning rule** -- if a node's bound is worse than the best complete solution found so far, discard the whole subtree",
                    "**When to prefer this over DP** -- large capacity values where the DP table would be too big, but a moderate number of items"
                ]},
                {"type": "callout", "kind": "tip", "title": "The bound is the whole trick", "value": "Using Fractional Knapsack's greedy solution as an upper bound for 0/1 Knapsack is a great example of how two algorithms from completely different families (greedy and branch & bound) can combine -- the greedy algorithm doesn't solve the harder problem, but it gives a cheap, useful estimate that makes the harder problem's search tree much smaller."},
                {"type": "code", "language": "python", "value": "class Node:\n    def __init__(self, level, profit, weight, bound):\n        self.level = level\n        self.profit = profit\n        self.weight = weight\n        self.bound = bound\n\ndef calculate_bound(node, n, capacity, items):\n    if node.weight >= capacity:\n        return 0\n    profit_bound = node.profit\n    j = node.level + 1\n    total_weight = node.weight\n\n    while j < n and total_weight + items[j][1] <= capacity:\n        total_weight += items[j][1]\n        profit_bound += items[j][0]\n        j += 1\n\n    if j < n:\n        profit_bound += (capacity - total_weight) * items[j][0] / items[j][1]\n\n    return profit_bound\n\ndef knapsack_branch_and_bound(values, weights, capacity):\n    items = sorted(zip(values, weights), key=lambda x: x[0] / x[1], reverse=True)\n    n = len(items)\n\n    queue = [Node(-1, 0, 0, 0)]\n    max_profit = 0\n\n    while queue:\n        node = queue.pop()\n        if node.level == n - 1:\n            continue\n\n        # Branch: include next item\n        next_level = node.level + 1\n        include_weight = node.weight + items[next_level][1]\n        include_profit = node.profit + items[next_level][0]\n\n        if include_weight <= capacity and include_profit > max_profit:\n            max_profit = include_profit\n\n        include_bound = calculate_bound(Node(next_level, include_profit, include_weight, 0), n, capacity, items)\n        if include_bound > max_profit:\n            queue.append(Node(next_level, include_profit, include_weight, include_bound))\n\n        # Branch: exclude next item\n        exclude_bound = calculate_bound(Node(next_level, node.profit, node.weight, 0), n, capacity, items)\n        if exclude_bound > max_profit:\n            queue.append(Node(next_level, node.profit, node.weight, exclude_bound))\n\n    return max_profit\n\nprint(knapsack_branch_and_bound([60, 100, 120], [10, 20, 30], 50))  # 220 -- matches the DP answer"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: 0/1 Knapsack using Branch and Bound", "url": "https://www.geeksforgeeks.org/implementation-of-0-1-knapsack-using-branch-and-bound/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-branch-and-bound",
        "title": "Job Sequencing Max Profit",
        "difficulty": "medium",
        "description": "Given n jobs, each with a deadline and profit (space-separated deadlines on one line, space-separated profits on the next), find the maximum total profit achievable by scheduling jobs (each takes 1 unit of time, must finish by its deadline, only one job per time slot).",
        "starter_code": "def job_sequencing(deadlines, profits):\n    jobs = sorted(zip(deadlines, profits), key=lambda x: x[1], reverse=True)\n    max_deadline = max(deadlines)\n    slots = [False] * (max_deadline + 1)\n    total = 0\n    for deadline, profit in jobs:\n        for slot in range(min(deadline, max_deadline), 0, -1):\n            if not slots[slot]:\n                slots[slot] = True\n                total += profit\n                break\n    return total\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\ndeadlines = list(map(int, lines[0].split()))\nprofits = list(map(int, lines[1].split()))\nprint(job_sequencing(deadlines, profits))",
        "test_cases": [
            {"input": "2 1 2 1 3\n100 19 27 25 15", "expected_output": "142"},
            {"input": "1 1\n10 20", "expected_output": "20"},
            {"input": "1\n5", "expected_output": "5"}
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
