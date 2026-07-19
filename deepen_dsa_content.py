import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

NEW_CONTENT = {
    ("dsa-arrays", "Array Structures & Memory Addressing"): [
        {"type": "heading", "level": 3, "value": "Static vs Dynamic Arrays"},
        {"type": "text", "value": "A **static array** has a fixed size decided at creation time -- Python's built-in list is actually a **dynamic array**: when it runs out of room, it allocates a new, larger block (typically 1.125x-2x the old size) and copies every element over. This copy is `O(n)`, but because it happens infrequently, the *amortized* cost of appending stays `O(1)`."},
        {"type": "list", "ordered": False, "items": [
            "**Access by index** -- `O(1)`, direct address computation, no traversal needed",
            "**Search (unsorted)** -- `O(n)`, must check every element in the worst case",
            "**Search (sorted, binary search)** -- `O(log n)`",
            "**Insert/Delete at end** -- `O(1)` amortized (dynamic array)",
            "**Insert/Delete at start or middle** -- `O(n)`, every following element must shift"
        ]},
        {"type": "callout", "kind": "warning", "title": "Common Interview Trap", "value": "Interviewers love asking *'why is inserting at the front of an array slow?'* The answer: every existing element has to physically shift one slot to the right to make room, which touches all `n` elements -- hence `O(n)`, even though the insertion itself is one operation."},
        {"type": "code", "language": "python", "value": "# Amortized O(1) append -- Python resizes automatically\narr = []\nfor i in range(5):\n    arr.append(i)\n    print(f\"len={len(arr)}, id={id(arr)}\")\n\n# Insert at front is O(n) -- everything shifts right\narr.insert(0, -1)\nprint(arr)  # [-1, 0, 1, 2, 3, 4]"}
    ],
    ("dsa-arrays", "Hashing Concepts & Hash Functions"): [
        {"type": "heading", "level": 3, "value": "Collision Resolution Strategies"},
        {"type": "text", "value": "No hash function is perfect -- two different keys can map to the same index (a **collision**). The two dominant strategies to handle this are **chaining** (each bucket holds a small list of entries) and **open addressing** (probe for the next free slot). Python's `dict` uses open addressing internally."},
        {"type": "list", "ordered": False, "items": [
            "**Chaining** -- each array slot holds a linked list; collisions just append to that list. Simple, degrades gracefully, but has pointer overhead.",
            "**Open Addressing (Linear Probing)** -- on collision, check the next slot, then the next, until a free one is found. Cache-friendly, but prone to *clustering*.",
            "**Load Factor (a = n / capacity)** -- once this crosses a threshold (commonly 0.7), the table is resized and every key is rehashed."
        ]},
        {"type": "callout", "kind": "tip", "title": "Why average O(1), not worst-case O(1)", "value": "A poorly designed hash function that clusters all keys into one bucket degrades lookups to `O(n)` -- this is why interviewers ask *'what makes a good hash function?'*: it should be **deterministic**, **fast to compute**, and produce a **uniform distribution** across the table."},
        {"type": "code", "language": "python", "value": "# A minimal hash map using chaining\nclass SimpleHashMap:\n    def __init__(self, size=8):\n        self.size = size\n        self.buckets = [[] for _ in range(size)]\n\n    def _hash(self, key):\n        return hash(key) % self.size\n\n    def put(self, key, value):\n        idx = self._hash(key)\n        for pair in self.buckets[idx]:\n            if pair[0] == key:\n                pair[1] = value\n                return\n        self.buckets[idx].append([key, value])\n\n    def get(self, key):\n        idx = self._hash(key)\n        for k, v in self.buckets[idx]:\n            if k == key:\n                return v\n        raise KeyError(key)"}
    ],
    ("dsa-linkedlists", "Singly Linked List Representation"): [
        {"type": "heading", "level": 3, "value": "Node Structure & Pointer Chains"},
        {"type": "text", "value": "Unlike arrays, a linked list doesn't need contiguous memory -- each **node** stores its data plus a pointer to the next node. This means insertion/deletion at the head is `O(1)` (no shifting required), but random access degrades to `O(n)` since you must walk the chain from the head every time."},
        {"type": "list", "ordered": False, "items": [
            "**Access by index** -- `O(n)`, must traverse from head",
            "**Insert/Delete at head** -- `O(1)`, just rewire one pointer",
            "**Insert/Delete at tail** -- `O(n)` without a tail pointer, `O(1)` with one",
            "**Search** -- `O(n)`"
        ]},
        {"type": "callout", "kind": "important", "title": "Draw It Before You Code It", "value": "The #1 mistake in linked-list interview questions is losing track of a pointer mid-rewire (e.g. overwriting `.next` before saving a reference to the next node). Always draw the before/after pointer diagram on paper first."},
        {"type": "code", "language": "python", "value": "class Node:\n    def __init__(self, val):\n        self.val = val\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n\n    def insert_at_head(self, val):\n        new_node = Node(val)\n        new_node.next = self.head\n        self.head = new_node\n\n    def reverse(self):\n        prev, curr = None, self.head\n        while curr:\n            nxt = curr.next\n            curr.next = prev\n            prev = curr\n            curr = nxt\n        self.head = prev"},
        {"type": "resource_link", "label": "\ud83d\udcd6 Visualize linked list operations interactively", "url": "https://visualgo.net/en/list"}
    ],
    ("dsa-trees", "Binary Search Trees (BST) & Properties"): [
        {"type": "heading", "level": 3, "value": "The BST Invariant"},
        {"type": "text", "value": "A **Binary Search Tree** maintains one core invariant at every node: everything in the **left subtree** is smaller, everything in the **right subtree** is larger. This ordering is what makes search, insert, and delete run in `O(log n)` on a **balanced** tree -- each comparison eliminates roughly half the remaining nodes, just like binary search on a sorted array."},
        {"type": "list", "ordered": False, "items": [
            "**Search / Insert / Delete (balanced)** -- `O(log n)`",
            "**Search / Insert / Delete (worst case, unbalanced/skewed)** -- `O(n)`, degrades to a linked list",
            "**In-order traversal** -- visits nodes in sorted order, `O(n)`"
        ]},
        {"type": "callout", "kind": "warning", "title": "The Skewed Tree Trap", "value": "Inserting sorted data (`1,2,3,4,5...`) into a plain BST produces a **degenerate tree** -- effectively a linked list with `O(n)` operations. This is exactly why self-balancing variants like **AVL trees** and **Red-Black trees** exist -- they rebalance on every insert/delete to guarantee `O(log n)`."},
        {"type": "code", "language": "python", "value": "class TreeNode:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n\ndef insert(root, val):\n    if root is None:\n        return TreeNode(val)\n    if val < root.val:\n        root.left = insert(root.left, val)\n    else:\n        root.right = insert(root.right, val)\n    return root\n\ndef inorder(root, result):\n    if root:\n        inorder(root.left, result)\n        result.append(root.val)\n        inorder(root.right, result)\n    return result"},
        {"type": "resource_link", "label": "\ud83d\udcd6 Visualize BST insert/delete interactively", "url": "https://www.cs.usfca.edu/~galles/visualization/BST.html"}
    ],
    ("dsa-sorting", "Divide & Conquer Sorting"): [
        {"type": "heading", "level": 3, "value": "Merge Sort vs Quick Sort"},
        {"type": "text", "value": "Both algorithms use **divide and conquer** but make different tradeoffs. **Merge Sort** splits the array in half, recursively sorts each half, then merges -- always `O(n log n)`, but needs `O(n)` extra space. **Quick Sort** picks a pivot, partitions around it, and recurses -- `O(n log n)` on average with `O(log n)` space, but degrades to `O(n^2)` on a bad pivot choice (e.g. always picking the first element on already-sorted data)."},
        {"type": "list", "ordered": False, "items": [
            "**Merge Sort** -- `O(n log n)` guaranteed, `O(n)` space, **stable**",
            "**Quick Sort** -- `O(n log n)` average / `O(n^2)` worst case, `O(log n)` space, **not stable**",
            "**Heap Sort** -- `O(n log n)` guaranteed, `O(1)` space, **not stable**"
        ]},
        {"type": "callout", "kind": "tip", "title": "Why randomized pivots matter", "value": "Randomizing the pivot choice in Quick Sort makes the `O(n^2)` worst case astronomically unlikely on any real input, rather than being trivially triggerable by already-sorted data."},
        {"type": "code", "language": "python", "value": "def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(left, right):\n    result, i, j = [], 0, 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i]); i += 1\n        else:\n            result.append(right[j]); j += 1\n    return result + left[i:] + right[j:]"}
    ],
}

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    for (topic_slug, sub_title), new_blocks in NEW_CONTENT.items():
        doc = await db.topics.find_one({"slug": topic_slug})
        if not doc:
            print(f"SKIP -- topic not found: {topic_slug}")
            continue
        updated = False
        for sub in doc.get("subtopics", []):
            if sub.get("title") == sub_title:
                existing = sub.get("content_blocks", [])
                resource_blocks = [b for b in existing if b.get("type") == "resource_link"]
                other_blocks = [b for b in existing if b.get("type") != "resource_link"]
                sub["content_blocks"] = other_blocks + new_blocks + resource_blocks
                updated = True
        if updated:
            await db.topics.replace_one({"_id": doc["_id"]}, doc)
            print(f"Updated: [{topic_slug}] {sub_title}")
        else:
            print(f"SKIP -- subtopic not found: [{topic_slug}] {sub_title}")

asyncio.run(main())
