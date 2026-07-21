import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-np-completeness",
    "title": "NP-Completeness & Algorithm Complexity Theory",
    "difficulty": "advanced",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "P, NP, and the Central Open Question",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Two Different Kinds of 'Hard'"},
                {"type": "text", "value": "**P** is the class of problems solvable in polynomial time -- sorting, shortest path, everything we've covered so far with clean `O(n log n)` or `O(n^3)` bounds. **NP** is the class of problems whose *solutions* can be **verified** in polynomial time, even if no one knows how to *find* a solution quickly. Every problem in P is trivially in NP (if you can solve it fast, you can certainly verify a solution fast) -- but whether every problem in NP is also in P is the single most famous open question in computer science: **does P = NP?** Most computer scientists believe P != NP, but nobody has proven it either way, and there's a $1,000,000 Millennium Prize waiting for whoever does."},
                {"type": "list", "ordered": False, "items": [
                    "**P** -- solvable in polynomial time (e.g. sorting, shortest path, matrix multiplication)",
                    "**NP** -- solution *verifiable* in polynomial time, even if finding one might take exponential time (e.g. Sudoku, given a filled board, checking it's valid is fast, but finding the solution might not be)",
                    "**NP-Hard** -- at least as hard as every problem in NP; may or may not itself be in NP",
                    "**NP-Complete** -- in NP, AND every other NP problem can be reduced to it in polynomial time -- these are the 'hardest problems in NP'"
                ]},
                {"type": "callout", "kind": "important", "title": "Why this matters practically", "value": "Recognizing that a problem is NP-Complete is genuinely useful information -- it tells you to stop searching for a fast exact algorithm and instead reach for approximation algorithms, heuristics, or exponential algorithms with good pruning (like the Branch & Bound and Backtracking we just covered), because no one has found (and most believe no one will find) a polynomial solution."},
                {"type": "code", "language": "python", "value": "# Verifying a Sudoku solution IS in P (fast), even though SOLVING Sudoku is NP-Complete\ndef is_valid_sudoku(board):\n    def valid_group(cells):\n        nums = [c for c in cells if c != 0]\n        return len(nums) == len(set(nums))\n\n    for row in board:\n        if not valid_group(row):\n            return False\n    for col in range(9):\n        if not valid_group([board[row][col] for row in range(9)]):\n            return False\n    for box_row in range(0, 9, 3):\n        for box_col in range(0, 9, 3):\n            cells = [board[box_row+i][box_col+j] for i in range(3) for j in range(3)]\n            if not valid_group(cells):\n                return False\n    return True\n\n# This check is O(1) relative to board size (fixed 9x9) -- fast verification,\n# even though finding a solution from scratch is a completely different, much harder problem."},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: P, NP, CoNP, NP hard and NP complete", "url": "https://www.geeksforgeeks.org/p-np-conp-np-hard-and-np-complete/"}
            ]
        },
        {
            "title": "Reductions: Proving a Problem is NP-Hard",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Borrowing Hardness From a Known-Hard Problem"},
                {"type": "text", "value": "You almost never prove NP-Hardness from first principles. Instead, you use a **reduction**: show that if you could solve your new problem quickly, you could use that to solve an *already-known* NP-Hard problem quickly too -- which would be a contradiction (assuming P != NP). This is exactly how the whole web of NP-Complete problems was built, starting from the **Cook-Levin theorem**, which proved that **Boolean Satisfiability (SAT)** is NP-Complete -- every other NP-Complete proof since then chains back to SAT (or another already-proven problem) through a sequence of reductions."},
                {"type": "list", "ordered": False, "items": [
                    "**SAT (Boolean Satisfiability)** -- the first problem proven NP-Complete (Cook-Levin theorem, 1971); given a boolean formula, is there an assignment of variables making it true?",
                    "**3-SAT** -- SAT restricted to clauses of exactly 3 literals; still NP-Complete, and the most common starting point for other reductions since it's simpler to work with",
                    "**Common NP-Complete problems (all reduce from SAT/3-SAT)** -- Traveling Salesman (decision version), Graph Coloring, Hamiltonian Path, Subset Sum, Clique",
                    "**A reduction shows equivalence in difficulty, not similarity in appearance** -- Graph Coloring and SAT look nothing alike, but a valid reduction between them proves they're equally hard"
                ]},
                {"type": "callout", "kind": "info", "title": "Why we covered Graph Coloring and Subset Sum earlier", "value": "This is the payoff for two topics from earlier in the DSA sequence: Graph Coloring (in Backtracking) and Subset Sum (in Backtracking) are both NP-Complete problems. That's exactly why we solve them with backtracking/branch & bound rather than a clean polynomial algorithm -- no such algorithm is known to exist, and most computer scientists believe none does."},
                {"type": "code", "language": "python", "value": "# Illustrative sketch of a reduction idea (not a full formal proof):\n# Subset Sum reduces FROM a simpler NP-Complete problem (Partition Problem)\n# by observing: partitioning a set into two equal-sum halves is equivalent\n# to asking 'does some subset sum to exactly half the total?' -- a Subset\n# Sum instance. If you could solve Subset Sum quickly for ANY input, you\n# could solve Partition quickly too, by just constructing this specific input.\n\ndef partition_via_subset_sum(nums):\n    total = sum(nums)\n    if total % 2 != 0:\n        return False  # can't split into two equal halves\n    target = total // 2\n\n    # Reduction: solving 'subset sums to target' answers the partition question\n    def subset_sum_exists(nums, target):\n        def backtrack(i, remaining):\n            if remaining == 0:\n                return True\n            if remaining < 0 or i == len(nums):\n                return False\n            return backtrack(i+1, remaining - nums[i]) or backtrack(i+1, remaining)\n        return backtrack(0, target)\n\n    return subset_sum_exists(nums, target)\n\nprint(partition_via_subset_sum([1, 5, 11, 5]))  # True -- {1, 5, 5} and {11}"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Cook-Levin Theorem", "url": "https://www.geeksforgeeks.org/cook-levin-theorem/"}
            ]
        },
        {
            "title": "Living With NP-Hardness: Approximation & Heuristics",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "What to Actually Do When a Problem Is NP-Hard"},
                {"type": "text", "value": "Knowing a problem is NP-Hard doesn't mean giving up -- it means changing strategy. In practice, four approaches dominate: **exact exponential algorithms with strong pruning** (Backtracking, Branch & Bound -- what we already covered), **approximation algorithms** (provably get within some factor of optimal, in polynomial time), **heuristics** (no guarantee, but work well in practice -- simulated annealing, genetic algorithms), and **restricting the input** (many NP-Hard problems become polynomial on special-case inputs, e.g. Vertex Cover is polynomial on trees even though it's NP-Hard in general)."},
                {"type": "list", "ordered": False, "items": [
                    "**Exact with pruning** -- Backtracking/Branch & Bound, exponential worst case but often fast in practice",
                    "**Approximation algorithms** -- e.g. a 2-approximation for Vertex Cover runs in polynomial time and guarantees a solution at most 2x the optimal size",
                    "**Heuristics** -- no worst-case guarantee at all, but often excellent real-world performance (simulated annealing for TSP, genetic algorithms for scheduling)",
                    "**Special-case restrictions** -- many NP-Hard problems become tractable if the input graph is a tree, is planar, or has bounded size in some dimension"
                ]},
                {"type": "callout", "kind": "tip", "title": "The practical takeaway for interviews and real systems", "value": "If you're asked to design a system around an NP-Hard problem (e.g. 'optimize delivery routes for 10,000 packages'), the expected answer is never 'solve it exactly' -- it's recognizing the problem's hardness and proposing a reasonable approximation or heuristic, which is itself a signal of strong CS fundamentals."},
                {"type": "code", "language": "python", "value": "# A simple 2-approximation algorithm for Vertex Cover\n# (NP-Hard exactly, but this greedy approach guarantees <= 2x the optimal size)\ndef vertex_cover_approx(edges):\n    cover = set()\n    remaining_edges = set(edges)\n\n    while remaining_edges:\n        u, v = remaining_edges.pop()  # pick any remaining edge\n        cover.add(u)\n        cover.add(v)\n        # Remove every edge covered by adding both endpoints\n        remaining_edges = {(a, b) for (a, b) in remaining_edges if a not in (u, v) and b not in (u, v)}\n\n    return cover\n\nedges = [(1, 2), (2, 3), (3, 4), (4, 5)]\nprint(vertex_cover_approx(edges))  # guaranteed <= 2x optimal, computed in polynomial time"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Approximation Algorithms", "url": "https://www.geeksforgeeks.org/approximation-algorithms/"},
                {"type": "resource_link", "label": "\U0001F4D6 Free Textbook: Algorithms (Jeff Erickson) -- NP-Hardness chapter", "url": "https://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffErickson.pdf"}
            ]
        }
    ]
}

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    existing = await db.topics.find_one({"slug": TOPIC["slug"]})
    if existing:
        print("SKIP -- topic already exists:", TOPIC["slug"])
    else:
        await db.topics.insert_one(TOPIC)
        print("Inserted topic:", TOPIC["slug"])
        print("Note: no practice problems for this topic -- it is conceptual/theory-focused by design")

asyncio.run(main())
