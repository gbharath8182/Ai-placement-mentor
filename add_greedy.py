import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-greedy",
    "title": "Greedy Algorithms",
    "difficulty": "intermediate",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Activity Selection & Interval Scheduling",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Making the Locally Best Choice"},
                {"type": "text", "value": "A **greedy algorithm** builds a solution one step at a time, always picking whatever looks best *right now*, without reconsidering earlier choices. This only produces a globally optimal answer for problems with the **greedy-choice property** -- a locally optimal choice leads to a globally optimal solution. The classic example is **Activity Selection**: given a set of activities with start/end times, select the maximum number that don't overlap. The greedy insight: always pick the activity that **finishes earliest** -- this leaves the most room for future activities."},
                {"type": "list", "ordered": False, "items": [
                    "**Sort by finish time** -- `O(n log n)`, dominates the total cost",
                    "**Greedy selection pass** -- `O(n)` after sorting",
                    "**Why 'earliest finish' beats 'shortest duration'** -- a short activity in the middle of the day can block more future activities than a longer one that ends early"
                ]},
                {"type": "callout", "kind": "warning", "title": "Greedy doesn't always work", "value": "Greedy fails on problems without the greedy-choice property -- the classic counterexample is **0/1 Knapsack** (you can't take a fraction of an item), where a locally-best choice can lock you out of the true optimum. That's exactly why 0/1 Knapsack needs Dynamic Programming instead, covered in the next topic."},
                {"type": "code", "language": "python", "value": "def activity_selection(activities):\n    # activities: list of (start, end)\n    activities = sorted(activities, key=lambda x: x[1])  # sort by finish time\n    selected = [activities[0]]\n    last_end = activities[0][1]\n\n    for start, end in activities[1:]:\n        if start >= last_end:\n            selected.append((start, end))\n            last_end = end\n\n    return selected\n\nactivities = [(1, 4), (3, 5), (0, 6), (5, 7), (3, 9), (5, 9), (6, 10), (8, 11), (8, 12), (2, 14), (12, 16)]\nprint(activity_selection(activities))"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Activity Selection Problem", "url": "https://www.geeksforgeeks.org/activity-selection-problem-greedy-algo-1/"}
            ]
        },
        {
            "title": "Fractional Knapsack",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "When Taking Fractions Is Allowed"},
                {"type": "text", "value": "Given items with a weight and value, and a knapsack with a maximum capacity, **Fractional Knapsack** allows taking any fraction of an item (unlike 0/1 Knapsack). This relaxation is exactly what makes the greedy approach work: sort items by **value-to-weight ratio**, and greedily take as much as possible of the highest-ratio item first, taking a fraction of the last item if it doesn't fully fit."},
                {"type": "list", "ordered": False, "items": [
                    "**Sort by value/weight ratio** -- `O(n log n)`",
                    "**Greedy fill pass** -- `O(n)`",
                    "**Guaranteed optimal** -- unlike 0/1 Knapsack, the fractional version always has a greedy solution that IS the true optimum"
                ]},
                {"type": "callout", "kind": "tip", "title": "The ratio is the key insight", "value": "Value-to-weight ratio measures 'value density' -- filling the knapsack with the densest items first always beats any other order, because every unit of capacity used on a lower-ratio item is capacity not used on a higher-ratio one."},
                {"type": "code", "language": "python", "value": "def fractional_knapsack(items, capacity):\n    # items: list of (value, weight)\n    items = sorted(items, key=lambda x: x[0] / x[1], reverse=True)\n    total_value = 0.0\n    remaining = capacity\n\n    for value, weight in items:\n        if remaining <= 0:\n            break\n        take = min(weight, remaining)\n        fraction = take / weight\n        total_value += value * fraction\n        remaining -= take\n\n    return total_value\n\nitems = [(60, 10), (100, 20), (120, 30)]  # (value, weight)\nprint(fractional_knapsack(items, 50))  # 240.0"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Fractional Knapsack Problem", "url": "https://www.geeksforgeeks.org/fractional-knapsack-problem/"}
            ]
        },
        {
            "title": "Huffman Coding & Compression",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Optimal Prefix-Free Compression"},
                {"type": "text", "value": "**Huffman Coding** assigns shorter binary codes to more frequent characters and longer codes to rarer ones, minimizing total encoded length -- the core idea behind formats like ZIP and JPEG. It builds a binary tree bottom-up: repeatedly take the two lowest-frequency nodes (using a min-heap) and merge them into a new parent node, until only one tree remains. The path from root to each leaf gives that character's code."},
                {"type": "list", "ordered": False, "items": [
                    "**Build the tree** -- `O(n log n)` using a min-heap, where n is the number of distinct characters",
                    "**Prefix-free property** -- no character's code is a prefix of another's, so encoded data can be decoded unambiguously without delimiters",
                    "**Why frequency matters** -- the more skewed the character frequencies, the more compression Huffman achieves versus fixed-length encoding (e.g. plain ASCII)"
                ]},
                {"type": "callout", "kind": "important", "title": "Why this is greedy", "value": "At every merge step, Huffman always combines the two *currently* least-frequent nodes -- a purely local decision. It provably produces the global optimum for prefix-free codes, which is a genuinely elegant example of the greedy-choice property holding for a non-obvious problem."},
                {"type": "code", "language": "python", "value": "import heapq\nfrom collections import Counter\n\nclass Node:\n    def __init__(self, char, freq):\n        self.char = char\n        self.freq = freq\n        self.left = None\n        self.right = None\n    def __lt__(self, other):\n        return self.freq < other.freq\n\ndef build_huffman_tree(text):\n    freq = Counter(text)\n    heap = [Node(ch, f) for ch, f in freq.items()]\n    heapq.heapify(heap)\n\n    while len(heap) > 1:\n        left = heapq.heappop(heap)\n        right = heapq.heappop(heap)\n        merged = Node(None, left.freq + right.freq)\n        merged.left, merged.right = left, right\n        heapq.heappush(heap, merged)\n\n    return heap[0]\n\ndef build_codes(node, prefix=\"\", codes=None):\n    if codes is None:\n        codes = {}\n    if node.char is not None:\n        codes[node.char] = prefix or \"0\"\n        return codes\n    build_codes(node.left, prefix + \"0\", codes)\n    build_codes(node.right, prefix + \"1\", codes)\n    return codes\n\ntree = build_huffman_tree(\"abracadabra\")\nprint(build_codes(tree))"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Huffman Coding", "url": "https://www.geeksforgeeks.org/huffman-coding-greedy-algo-3/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-greedy",
        "title": "Maximum Activities",
        "difficulty": "medium",
        "description": "Given n activities as space-separated start times on one line and end times on the next, find the maximum number of non-overlapping activities that can be selected.",
        "starter_code": "def max_activities(starts, ends):\n    activities = sorted(zip(starts, ends), key=lambda x: x[1])\n    count = 1\n    last_end = activities[0][1]\n    for s, e in activities[1:]:\n        if s >= last_end:\n            count += 1\n            last_end = e\n    return count\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nstarts = list(map(int, lines[0].split()))\nends = list(map(int, lines[1].split()))\nprint(max_activities(starts, ends))",
        "test_cases": [
            {"input": "1 3 0 5 8 5\n2 4 6 7 9 9", "expected_output": "4"},
            {"input": "1 2 3\n2 3 4", "expected_output": "3"},
            {"input": "1\n2", "expected_output": "1"}
        ]
    },
    {
        "topic_slug": "dsa-greedy",
        "title": "Fractional Knapsack Value",
        "difficulty": "medium",
        "description": "Given n items with space-separated values on one line and weights on the next, and a knapsack capacity on the third line, print the maximum total value achievable (as an integer, truncating any fraction) using fractional knapsack.",
        "starter_code": "def fractional_knapsack(values, weights, capacity):\n    items = sorted(zip(values, weights), key=lambda x: x[0] / x[1], reverse=True)\n    total = 0.0\n    remaining = capacity\n    for value, weight in items:\n        if remaining <= 0:\n            break\n        take = min(weight, remaining)\n        total += value * (take / weight)\n        remaining -= take\n    return int(total)\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nvalues = list(map(int, lines[0].split()))\nweights = list(map(int, lines[1].split()))\ncapacity = int(lines[2])\nprint(fractional_knapsack(values, weights, capacity))",
        "test_cases": [
            {"input": "60 100 120\n10 20 30\n50", "expected_output": "240"},
            {"input": "10\n5\n10", "expected_output": "10"},
            {"input": "10 20\n10 10\n5", "expected_output": "10"}
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
