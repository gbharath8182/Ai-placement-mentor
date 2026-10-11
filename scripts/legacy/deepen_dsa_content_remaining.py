import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

NEW_CONTENT = {
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
        {"type": "resource_link", "label": "\U0001F4D6 Visualize linked list operations interactively", "url": "https://visualgo.net/en/list"}
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
        {"type": "resource_link", "label": "\U0001F4D6 Visualize BST insert/delete interactively", "url": "https://www.cs.usfca.edu/~galles/visualization/BST.html"}
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

import sys
sys.path.insert(0, r"c:\Users\navaneeth\Ai-placement-mentor")
from backend.config import settings

async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]

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
