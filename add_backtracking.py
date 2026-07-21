import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-backtracking",
    "title": "Backtracking",
    "difficulty": "advanced",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Backtracking Fundamentals: N-Queens",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Try, Fail, Undo, Try Again"},
                {"type": "text", "value": "**Backtracking** explores all possible solutions by building them incrementally, and the moment a partial solution can't possibly lead to a valid answer, it **abandons that branch immediately** (prunes) and backs up to try the next option -- rather than wastefully exploring a doomed path to completion. The classic example is the **N-Queens problem**: place N queens on an N x N board so none attack each other. Instead of generating all `N^N` placements and checking each, backtracking places queens one row at a time and immediately abandons a row's placement if it conflicts with any queen already placed."},
                {"type": "list", "ordered": False, "items": [
                    "**Worst case time** -- exponential (`O(N!)` roughly for N-Queens), but pruning makes it far faster in practice than brute force",
                    "**Core pattern** -- choose -> explore recursively -> un-choose (backtrack) if it leads nowhere",
                    "**Constraint checking is what makes it fast** -- the earlier a branch can be pruned, the more work is saved"
                ]},
                {"type": "callout", "kind": "tip", "title": "Backtracking vs brute force", "value": "Brute force generates every complete candidate and checks validity at the end. Backtracking checks validity *as it builds*, abandoning invalid partial solutions immediately -- this pruning is the entire reason backtracking is tractable where brute force isn't."},
                {"type": "code", "language": "python", "value": "def solve_n_queens(n):\n    solutions = []\n    cols = set()\n    diag1 = set()  # row - col\n    diag2 = set()  # row + col\n    board = []\n\n    def backtrack(row):\n        if row == n:\n            solutions.append(board[:])\n            return\n        for col in range(n):\n            if col in cols or (row - col) in diag1 or (row + col) in diag2:\n                continue  # prune -- this placement conflicts, skip immediately\n            cols.add(col); diag1.add(row - col); diag2.add(row + col)\n            board.append(col)\n\n            backtrack(row + 1)\n\n            cols.remove(col); diag1.remove(row - col); diag2.remove(row + col)\n            board.pop()\n\n    backtrack(0)\n    return solutions\n\nprint(len(solve_n_queens(4)))  # 2 solutions for 4-Queens"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: N-Queen Problem", "url": "https://www.geeksforgeeks.org/n-queen-problem-backtracking-3/"}
            ]
        },
        {
            "title": "Subset Sum & Combination Search",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Exploring the Space of Subsets"},
                {"type": "text", "value": "**Subset Sum** asks: does any subset of a given set of numbers add up to a target value? Backtracking explores this by making a binary choice at each element -- include it or skip it -- and prunes the moment the running sum exceeds the target (assuming positive numbers). This same include/exclude recursive pattern underlies most 'find all combinations/subsets' problems."},
                {"type": "list", "ordered": False, "items": [
                    "**Without pruning** -- `O(2^n)`, every subset is a valid candidate to check",
                    "**With sum-based pruning** -- often much faster in practice, though worst case is still exponential",
                    "**Related pattern** -- Combination Sum, Partition Equal Subset Sum, and Power Set generation all use this same include/exclude backtracking shape"
                ]},
                {"type": "callout", "kind": "warning", "title": "Backtracking vs DP for Subset Sum", "value": "If you only need a yes/no answer (or the count of subsets), DP is usually faster (`O(n * target)` via a boolean/count table). Backtracking is the right tool when you need to enumerate the *actual subsets themselves*, since DP tables don't directly reconstruct every combination without extra bookkeeping."},
                {"type": "code", "language": "python", "value": "def subset_sum_exists(nums, target):\n    def backtrack(index, remaining):\n        if remaining == 0:\n            return True\n        if remaining < 0 or index == len(nums):\n            return False\n        # Include nums[index]\n        if backtrack(index + 1, remaining - nums[index]):\n            return True\n        # Exclude nums[index]\n        return backtrack(index + 1, remaining)\n\n    return backtrack(0, target)\n\ndef find_all_subsets(nums, target):\n    results = []\n    path = []\n\n    def backtrack(index, remaining):\n        if remaining == 0:\n            results.append(path[:])\n            return\n        if remaining < 0 or index == len(nums):\n            return\n        path.append(nums[index])\n        backtrack(index + 1, remaining - nums[index])\n        path.pop()\n        backtrack(index + 1, remaining)\n\n    backtrack(0, target)\n    return results\n\nprint(subset_sum_exists([3, 34, 4, 12, 5, 2], 9))  # True\nprint(find_all_subsets([2, 3, 5], 5))  # [[2, 3], [5]]"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Subset Sum Problem", "url": "https://www.geeksforgeeks.org/subset-sum-problem-dp-25/"}
            ]
        },
        {
            "title": "Graph Coloring",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Assigning Colors Without Conflicts"},
                {"type": "text", "value": "**Graph Coloring** assigns a color to each node such that no two adjacent nodes share a color, using at most `m` colors. This models real problems like register allocation in compilers (variables that are 'alive' at the same time can't share a register) and exam scheduling (courses with common students can't share a time slot). Backtracking tries each color for a node, checks if any neighbor already has that color, and prunes immediately on conflict."},
                {"type": "list", "ordered": False, "items": [
                    "**Worst case** -- `O(m^V)`, trying every color for every vertex",
                    "**Chromatic number** -- the minimum number of colors needed for a graph; finding it exactly is NP-Hard, so backtracking with a fixed `m` (checking 'can this be colored with m colors?') is the practical approach",
                    "**Real-world analogy** -- register allocation: build an 'interference graph' of variables that are live simultaneously, then color it with available CPU registers"
                ]},
                {"type": "callout", "kind": "info", "title": "Why this connects to NP-Completeness", "value": "Determining a graph's exact chromatic number is one of the classic NP-Hard problems -- there's no known polynomial-time algorithm, which is exactly why backtracking (exponential worst case, but practically fast with good pruning) remains the standard approach rather than something more efficient."},
                {"type": "code", "language": "python", "value": "def graph_coloring(graph, m, n):\n    # graph: adjacency matrix (n x n), m: number of colors\n    colors = [0] * n\n\n    def is_safe(node, color):\n        for neighbor in range(n):\n            if graph[node][neighbor] == 1 and colors[neighbor] == color:\n                return False\n        return True\n\n    def backtrack(node):\n        if node == n:\n            return True\n        for color in range(1, m + 1):\n            if is_safe(node, color):\n                colors[node] = color\n                if backtrack(node + 1):\n                    return True\n                colors[node] = 0  # undo -- backtrack\n        return False\n\n    if backtrack(0):\n        return colors\n    return None\n\ngraph = [\n    [0, 1, 1, 1],\n    [1, 0, 1, 0],\n    [1, 1, 0, 1],\n    [1, 0, 1, 0]\n]\nprint(graph_coloring(graph, 3, 4))  # a valid 3-coloring, e.g. [1, 2, 3, 2]"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Graph Coloring Problem", "url": "https://www.geeksforgeeks.org/graph-coloring-applications/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-backtracking",
        "title": "N-Queens Count",
        "difficulty": "hard",
        "description": "Given n, print the number of distinct solutions to the N-Queens problem.",
        "starter_code": "def solve_n_queens(n):\n    solutions = [0]\n    cols, diag1, diag2 = set(), set(), set()\n    def backtrack(row):\n        if row == n:\n            solutions[0] += 1\n            return\n        for col in range(n):\n            if col in cols or (row-col) in diag1 or (row+col) in diag2:\n                continue\n            cols.add(col); diag1.add(row-col); diag2.add(row+col)\n            backtrack(row+1)\n            cols.remove(col); diag1.remove(row-col); diag2.remove(row+col)\n    backtrack(0)\n    return solutions[0]\n\nimport sys\nn = int(sys.stdin.readline())\nprint(solve_n_queens(n))",
        "test_cases": [
            {"input": "4", "expected_output": "2"},
            {"input": "1", "expected_output": "1"},
            {"input": "8", "expected_output": "92"}
        ]
    },
    {
        "topic_slug": "dsa-backtracking",
        "title": "Subset Sum Exists",
        "difficulty": "medium",
        "description": "Given space-separated integers on one line and a target on the next, print 'true' if any subset sums to the target, else 'false'.",
        "starter_code": "def subset_sum_exists(nums, target):\n    def backtrack(index, remaining):\n        if remaining == 0:\n            return True\n        if remaining < 0 or index == len(nums):\n            return False\n        if backtrack(index+1, remaining - nums[index]):\n            return True\n        return backtrack(index+1, remaining)\n    return backtrack(0, target)\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nnums = list(map(int, lines[0].split()))\ntarget = int(lines[1])\nprint(str(subset_sum_exists(nums, target)).lower())",
        "test_cases": [
            {"input": "3 34 4 12 5 2\n9", "expected_output": "true"},
            {"input": "1 2 3\n7", "expected_output": "false"},
            {"input": "5\n5", "expected_output": "true"}
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
