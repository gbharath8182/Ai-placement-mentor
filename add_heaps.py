import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-heaps",
    "title": "Heaps & Priority Queues",
    "difficulty": "intermediate",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Heap Fundamentals: Max-Heap & Min-Heap",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "The Heap Property"},
                {"type": "text", "value": "A **heap** is a complete binary tree stored in a flat array, obeying one invariant everywhere: in a **Max-Heap**, every parent is >= its children; in a **Min-Heap**, every parent is <= its children. Because it's a *complete* tree (filled left to right, no gaps), it can be stored in a plain array with no pointers at all -- for a node at index `i`, its children live at `2i+1` and `2i+2`, and its parent at `(i-1)//2`."},
                {"type": "list", "ordered": False, "items": [
                    "**Peek min/max** -- `O(1)`, it's always at index 0",
                    "**Insert** -- `O(log n)`, add at the end and 'bubble up'",
                    "**Extract min/max** -- `O(log n)`, swap root with last element, remove last, 'bubble down'",
                    "**Build heap from n elements** -- `O(n)`, NOT `O(n log n)` -- a subtlety that surprises most people"
                ]},
                {"type": "callout", "kind": "important", "title": "A heap is NOT a sorted structure", "value": "Only the root is guaranteed to be the min/max -- the rest of the array has no overall order. This is exactly why in-order traversal doesn't apply to heaps the way it does to BSTs; you can only cheaply extract one end, not iterate in sorted order."},
                {"type": "code", "language": "python", "value": "import heapq\n\n# Python's heapq is a MIN-heap by default\nheap = []\nheapq.heappush(heap, 5)\nheapq.heappush(heap, 1)\nheapq.heappush(heap, 3)\nprint(heapq.heappop(heap))  # 1 -- smallest first\n\n# To simulate a MAX-heap, negate values on the way in and out\nmax_heap = []\nfor val in [5, 1, 3]:\n    heapq.heappush(max_heap, -val)\nprint(-heapq.heappop(max_heap))  # 5 -- largest first"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Binary Heap", "url": "https://www.geeksforgeeks.org/binary-heap/"}
            ]
        },
        {
            "title": "Heapify & Priority Queue Operations",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Building and Maintaining Heap Order"},
                {"type": "text", "value": "**Heapify** is the process of converting an arbitrary array into a valid heap. Doing it by inserting elements one at a time costs `O(n log n)`, but the classic bottom-up heapify algorithm -- starting from the last non-leaf node and sifting down -- achieves `O(n)` overall, because most nodes are near the bottom of the tree and need very few swaps."},
                {"type": "list", "ordered": False, "items": [
                    "**Sift down (bubble down)** -- used after extracting the root, or during heapify; compares a node to its children and swaps with the larger/smaller until the property holds",
                    "**Sift up (bubble up)** -- used after inserting at the end; compares a node to its parent and swaps upward until the property holds",
                    "**Priority Queue** -- a heap is the standard implementation; `decrease-key` (used in Dijkstra's algorithm) requires either a heap that supports key updates or a lazy-deletion trick"
                ]},
                {"type": "callout", "kind": "tip", "title": "Why heapify is O(n), not O(n log n)", "value": "Most nodes in a complete binary tree are leaves or near-leaves -- only `O(n/2)` nodes need to sift down at all, and the ones deepest in the tree (which are also most numerous) have the fewest levels to sift through. The math works out to a geometric series that sums to `O(n)`, not `O(n log n)`."},
                {"type": "code", "language": "python", "value": "def sift_down(arr, i, n):\n    while True:\n        smallest = i\n        left, right = 2*i + 1, 2*i + 2\n        if left < n and arr[left] < arr[smallest]:\n            smallest = left\n        if right < n and arr[right] < arr[smallest]:\n            smallest = right\n        if smallest == i:\n            break\n        arr[i], arr[smallest] = arr[smallest], arr[i]\n        i = smallest\n\ndef heapify(arr):\n    n = len(arr)\n    # Start from the last non-leaf node, work backward to root\n    for i in range(n // 2 - 1, -1, -1):\n        sift_down(arr, i, n)\n    return arr\n\nprint(heapify([5, 3, 8, 1, 9, 2]))  # valid min-heap array"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Heapify Algorithm", "url": "https://www.geeksforgeeks.org/heapify-method-in-python/"}
            ]
        },
        {
            "title": "Heap-Based Algorithms",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Where Heaps Actually Show Up"},
                {"type": "text", "value": "Heaps are the go-to structure whenever you need 'the k best/smallest/largest so far' without fully sorting everything. Two of the most common interview patterns: finding the Kth largest element using a fixed-size min-heap, and merging K sorted lists using a heap to always pick the smallest available head element next."},
                {"type": "list", "ordered": False, "items": [
                    "**Kth Largest Element** -- maintain a min-heap of size K; if a new element is bigger than the heap's root, swap it in -- `O(n log k)`, much better than sorting the whole array (`O(n log n)`) when k is small",
                    "**Merge K Sorted Lists** -- push the head of each list into a min-heap; repeatedly pop the smallest and push its successor -- `O(n log k)` where n is total elements across all lists",
                    "**Dijkstra's Shortest Path** -- uses a min-heap keyed by current shortest distance, always expanding the closest unvisited node next",
                    "**Median of a Data Stream** -- maintain a max-heap for the lower half and a min-heap for the upper half; the median is always at the top of one or both"
                ]},
                {"type": "callout", "kind": "warning", "title": "Don't over-reach for a heap", "value": "If you only need the single min/max once, a heap is overkill -- a simple linear scan is `O(n)` and simpler. Heaps earn their keep specifically when you need repeated min/max extraction, or a fixed-size 'top K' window as data streams in."},
                {"type": "code", "language": "python", "value": "import heapq\n\ndef kth_largest(nums, k):\n    heap = nums[:k]\n    heapq.heapify(heap)\n    for num in nums[k:]:\n        if num > heap[0]:\n            heapq.heapreplace(heap, num)\n    return heap[0]\n\nprint(kth_largest([3, 2, 1, 5, 6, 4], 2))  # 5 -- 2nd largest\n\ndef merge_k_sorted(lists):\n    heap = []\n    for i, lst in enumerate(lists):\n        if lst:\n            heapq.heappush(heap, (lst[0], i, 0))\n    result = []\n    while heap:\n        val, list_idx, elem_idx = heapq.heappop(heap)\n        result.append(val)\n        if elem_idx + 1 < len(lists[list_idx]):\n            nxt = lists[list_idx][elem_idx + 1]\n            heapq.heappush(heap, (nxt, list_idx, elem_idx + 1))\n    return result"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Applications of Heap Data Structure", "url": "https://www.geeksforgeeks.org/applications-of-heap-data-structure/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-heaps",
        "title": "Kth Largest Element in an Array",
        "difficulty": "medium",
        "description": "Given a space-separated list of integers and an integer k on the second line, find the kth largest element in the array.",
        "starter_code": "import heapq\n\ndef kth_largest(nums, k):\n    heap = nums[:k]\n    heapq.heapify(heap)\n    for num in nums[k:]:\n        if num > heap[0]:\n            heapq.heapreplace(heap, num)\n    return heap[0]\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nnums = list(map(int, lines[0].split()))\nk = int(lines[1])\nprint(kth_largest(nums, k))",
        "test_cases": [
            {"input": "3 2 1 5 6 4\n2", "expected_output": "5"},
            {"input": "3 2 3 1 2 4 5 5 6\n4", "expected_output": "4"},
            {"input": "1\n1", "expected_output": "1"}
        ]
    },
    {
        "topic_slug": "dsa-heaps",
        "title": "Is Valid Min-Heap Array",
        "difficulty": "easy",
        "description": "Given a space-separated array representing a binary tree in array form, determine if it satisfies the min-heap property (every parent <= its children). Print 'true' or 'false'.",
        "starter_code": "def is_min_heap(arr):\n    n = len(arr)\n    for i in range(n):\n        left, right = 2*i + 1, 2*i + 2\n        if left < n and arr[i] > arr[left]:\n            return False\n        if right < n and arr[i] > arr[right]:\n            return False\n    return True\n\nimport sys\narr = list(map(int, sys.stdin.readline().split()))\nprint(str(is_min_heap(arr)).lower())",
        "test_cases": [
            {"input": "1 3 2 5 4 6", "expected_output": "true"},
            {"input": "5 3 2 1 4", "expected_output": "false"},
            {"input": "1", "expected_output": "true"}
        ]
    },
    {
        "topic_slug": "dsa-heaps",
        "title": "Heapify an Array",
        "difficulty": "medium",
        "description": "Given a space-separated array of integers, convert it into a valid min-heap using an O(n) heapify and print the resulting array.",
        "starter_code": "def sift_down(arr, i, n):\n    while True:\n        smallest = i\n        left, right = 2*i + 1, 2*i + 2\n        if left < n and arr[left] < arr[smallest]:\n            smallest = left\n        if right < n and arr[right] < arr[smallest]:\n            smallest = right\n        if smallest == i:\n            break\n        arr[i], arr[smallest] = arr[smallest], arr[i]\n        i = smallest\n\ndef heapify(arr):\n    n = len(arr)\n    for i in range(n // 2 - 1, -1, -1):\n        sift_down(arr, i, n)\n    return arr\n\nimport sys\narr = list(map(int, sys.stdin.readline().split()))\nprint(' '.join(map(str, heapify(arr))))",
        "test_cases": [
            {"input": "5 3 8 1 9 2", "expected_output": "1 3 2 5 9 8"},
            {"input": "1 2 3", "expected_output": "1 2 3"},
            {"input": "9", "expected_output": "9"}
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
