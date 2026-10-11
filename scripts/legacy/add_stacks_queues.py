import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-stacks-queues",
    "title": "Stacks & Queues",
    "difficulty": "beginner",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Stack Fundamentals & LIFO Operations",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Last-In-First-Out"},
                {"type": "text", "value": "A **stack** only allows access to its most recently added element -- think of a stack of plates, you can only take from the top. This constraint is exactly what makes stacks useful: they naturally model *nested* structures like function calls, undo history, and matching brackets."},
                {"type": "list", "ordered": False, "items": [
                    "**Push (add to top)** -- `O(1)`",
                    "**Pop (remove from top)** -- `O(1)`",
                    "**Peek (view top without removing)** -- `O(1)`",
                    "**Search for arbitrary element** -- `O(n)`"
                ]},
                {"type": "callout", "kind": "tip", "title": "The Call Stack Connection", "value": "Every recursive function call you write is secretly using a stack -- each call pushes a new frame, and returning pops it off. This is also why deep, unbounded recursion causes a `StackOverflowError`."},
                {"type": "code", "language": "python", "value": "# Python lists work perfectly as stacks\nstack = []\nstack.append(1)   # push\nstack.append(2)\nstack.append(3)\nprint(stack.pop())  # 3 -- LIFO\nprint(stack[-1])    # peek: 2\n\n# Classic use case: Valid Parentheses\ndef is_valid(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in '([{':\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return not stack"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Stack Data Structure", "url": "https://www.geeksforgeeks.org/stack-data-structure/"}
            ]
        },
        {
            "title": "Queue Variants & Circular Buffers",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "First-In-First-Out"},
                {"type": "text", "value": "A **queue** processes elements in the order they arrived -- like a line at a checkout counter. Python's naive `list.pop(0)` is `O(n)` because every remaining element shifts left; `collections.deque` avoids this with `O(1)` operations on both ends."},
                {"type": "list", "ordered": False, "items": [
                    "**Enqueue (add to back)** -- `O(1)` with `deque`, `O(n)` with a plain list append at index 0",
                    "**Dequeue (remove from front)** -- `O(1)` with `deque`, `O(n)` with `list.pop(0)`",
                    "**Circular Queue** -- fixed-size buffer that wraps around, avoiding wasted space from a naive front pointer",
                    "**Priority Queue (heap-backed)** -- dequeues by priority, not arrival order, `O(log n)`"
                ]},
                {"type": "callout", "kind": "warning", "title": "Don't use list.pop(0) for queues", "value": "It's a classic beginner mistake: `my_list.pop(0)` looks innocent but is `O(n)` because every remaining element has to shift. Always reach for `collections.deque` when you need a real queue."},
                {"type": "code", "language": "python", "value": "from collections import deque\n\nq = deque()\nq.append(1)       # enqueue\nq.append(2)\nq.append(3)\nprint(q.popleft())  # 1 -- FIFO, O(1)\n\n# Queue using two stacks (classic interview question)\nclass QueueFromStacks:\n    def __init__(self):\n        self.in_stack = []\n        self.out_stack = []\n\n    def enqueue(self, x):\n        self.in_stack.append(x)\n\n    def dequeue(self):\n        if not self.out_stack:\n            while self.in_stack:\n                self.out_stack.append(self.in_stack.pop())\n        return self.out_stack.pop()"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Queue Data Structure", "url": "https://www.geeksforgeeks.org/queue-data-structure/"}
            ]
        },
        {
            "title": "Monotonic Stacks -- Advanced Pattern",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Keeping the Stack Ordered"},
                {"type": "text", "value": "A **monotonic stack** maintains elements in strictly increasing or decreasing order by popping anything that would violate that order before pushing. This turns an apparent `O(n^2)` brute-force scan (for every element, look at every other element) into a single `O(n)` pass, because each element is pushed and popped at most once."},
                {"type": "list", "ordered": False, "items": [
                    "**Overall time complexity** -- `O(n)`, even though it looks like nested work at first glance",
                    "**Classic use cases** -- Next Greater Element, Daily Temperatures, Largest Rectangle in Histogram",
                    "**Decreasing stack** -- finds the next *greater* element to the right",
                    "**Increasing stack** -- finds the next *smaller* element to the right"
                ]},
                {"type": "callout", "kind": "important", "title": "Recognizing the pattern", "value": "If a problem asks *'for each element, find the next element to the right that is greater/smaller'*, that's almost always a monotonic stack in disguise -- don't reach for nested loops."},
                {"type": "code", "language": "python", "value": "def next_greater_element(nums):\n    result = [-1] * len(nums)\n    stack = []  # stores indices, kept decreasing by value\n\n    for i, num in enumerate(nums):\n        while stack and nums[stack[-1]] < num:\n            idx = stack.pop()\n            result[idx] = num\n        stack.append(i)\n\n    return result\n\nprint(next_greater_element([2, 1, 2, 4, 3]))  # [4, 2, 4, -1, -1]"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Monotonic Stack Pattern", "url": "https://www.geeksforgeeks.org/introduction-to-monotonic-stack/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-stacks-queues",
        "title": "Valid Parentheses",
        "difficulty": "easy",
        "description": "Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. An input string is valid if brackets close in the correct order and every opening bracket has a matching closing bracket of the same type.",
        "starter_code": "def is_valid(s):\n    # Write your solution here\n    pass\n\nimport sys\nline = sys.stdin.readline().strip()\nprint(str(is_valid(line)).lower())",
        "test_cases": [
            {"input": "()", "expected_output": "true"},
            {"input": "()[]{}", "expected_output": "true"},
            {"input": "(]", "expected_output": "false"},
            {"input": "([)]", "expected_output": "false"},
            {"input": "{[]}", "expected_output": "true"}
        ]
    },
    {
        "topic_slug": "dsa-stacks-queues",
        "title": "Implement Queue using Stacks",
        "difficulty": "medium",
        "description": "Implement a first-in-first-out (FIFO) queue using only two stacks. Given a sequence of space-separated integers representing enqueue operations, print the dequeue order.",
        "starter_code": "def process(nums):\n    # Use two stacks to simulate a queue, return dequeue order\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.readline().split()))\nprint(' '.join(map(str, process(nums))))",
        "test_cases": [
            {"input": "1 2 3", "expected_output": "1 2 3"},
            {"input": "5 4 3 2 1", "expected_output": "5 4 3 2 1"},
            {"input": "7", "expected_output": "7"}
        ]
    },
    {
        "topic_slug": "dsa-stacks-queues",
        "title": "Next Greater Element",
        "difficulty": "medium",
        "description": "Given a space-separated list of integers, for each element find the next element to its right that is strictly greater. If none exists, output -1 for that position. Print results space-separated.",
        "starter_code": "def next_greater(nums):\n    # Use a monotonic stack\n    pass\n\nimport sys\nnums = list(map(int, sys.stdin.readline().split()))\nprint(' '.join(map(str, next_greater(nums))))",
        "test_cases": [
            {"input": "2 1 2 4 3", "expected_output": "4 2 4 -1 -1"},
            {"input": "1 2 3 4", "expected_output": "2 3 4 -1"},
            {"input": "4 3 2 1", "expected_output": "-1 -1 -1 -1"}
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
