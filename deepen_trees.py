import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

NEW_SUBTOPICS = [
    {
        "title": "Tree Traversals (DFS & BFS)",
        "difficulty": "beginner",
        "content_blocks": [
            {"type": "heading", "level": 2, "value": "Visiting Every Node, In Order"},
            {"type": "text", "value": "There are four standard ways to visit every node in a tree, and each answers a different question. The three **DFS (depth-first)** orders differ only in *when* you process the current node relative to its children; **BFS (breadth-first)** is a completely different strategy that processes level by level using a queue instead of recursion."},
            {"type": "list", "ordered": False, "items": [
                "**Pre-order (Node -> Left -> Right)** -- used to copy/serialize a tree, since the root is processed first",
                "**In-order (Left -> Node -> Right)** -- on a BST, this visits nodes in **sorted order** -- the single most useful traversal for BSTs",
                "**Post-order (Left -> Right -> Node)** -- used when children must be processed before the parent, e.g. deleting a tree or evaluating an expression tree",
                "**BFS / Level-order** -- visits nodes level by level using a queue; used for shortest-path-in-unweighted-tree style problems"
            ]},
            {"type": "callout", "kind": "tip", "title": "Why in-order sorts a BST", "value": "Because a BST guarantees left < node < right at every level, visiting Left, then Node, then Right recursively produces values in strictly increasing order -- this is the mechanism behind 'flatten a BST into a sorted array' problems."},
            {"type": "code", "language": "python", "value": "from collections import deque\n\nclass TreeNode:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n\ndef preorder(root, out):\n    if root:\n        out.append(root.val)\n        preorder(root.left, out)\n        preorder(root.right, out)\n\ndef inorder(root, out):\n    if root:\n        inorder(root.left, out)\n        out.append(root.val)\n        inorder(root.right, out)\n\ndef postorder(root, out):\n    if root:\n        postorder(root.left, out)\n        postorder(root.right, out)\n        out.append(root.val)\n\ndef level_order(root):\n    if not root:\n        return []\n    result, q = [], deque([root])\n    while q:\n        level = []\n        for _ in range(len(q)):\n            node = q.popleft()\n            level.append(node.val)\n            if node.left: q.append(node.left)\n            if node.right: q.append(node.right)\n        result.append(level)\n    return result"},
            {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Tree Traversals", "url": "https://www.geeksforgeeks.org/tree-traversals-inorder-preorder-and-postorder/"}
        ]
    },
    {
        "title": "Self-Balancing Trees: AVL & Red-Black",
        "difficulty": "advanced",
        "content_blocks": [
            {"type": "heading", "level": 2, "value": "Guaranteeing O(log n) Even in the Worst Case"},
            {"type": "text", "value": "A plain BST degrades to `O(n)` if data arrives in sorted order. **Self-balancing trees** fix this by restructuring themselves after every insert/delete, guaranteeing `O(log n)` operations no matter the input order. **AVL trees** are the strictest: they track a **balance factor** (height of left subtree minus height of right subtree) at every node and rebalance the instant it exceeds ±1. **Red-Black trees** are looser (allowing up to 2x height imbalance between subtrees), which means fewer rotations on insert/delete -- this is why most language standard libraries (C++ `map`, Java `TreeMap`) use Red-Black trees rather than AVL."},
            {"type": "list", "ordered": False, "items": [
                "**AVL balance factor** -- must stay in {-1, 0, 1} at every node; violated -> rotate",
                "**LL / RR rotation** -- single rotation, fixes a straight-line imbalance",
                "**LR / RL rotation** -- double rotation, fixes a zig-zag imbalance",
                "**AVL vs Red-Black tradeoff** -- AVL is more strictly balanced (faster lookups), Red-Black rebalances less often (faster inserts/deletes) -- this is exactly why databases favor Red-Black-like structures for write-heavy workloads"
            ]},
            {"type": "callout", "kind": "important", "title": "When rotations trigger", "value": "A rotation only fires when a node's balance factor leaves {-1, 0, 1} *after* an insert or delete. You don't rebalance the whole tree -- only the lowest unbalanced ancestor needs a rotation, which is why AVL inserts stay `O(log n)` even with rebalancing included."},
            {"type": "code", "language": "python", "value": "class AVLNode:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n        self.height = 1\n\ndef height(node):\n    return node.height if node else 0\n\ndef balance_factor(node):\n    return height(node.left) - height(node.right) if node else 0\n\ndef update_height(node):\n    node.height = 1 + max(height(node.left), height(node.right))\n\ndef rotate_right(y):\n    x = y.left\n    y.left = x.right\n    x.right = y\n    update_height(y)\n    update_height(x)\n    return x\n\ndef rotate_left(x):\n    y = x.right\n    x.right = y.left\n    y.left = x\n    update_height(x)\n    update_height(y)\n    return y\n\ndef insert(node, val):\n    if not node:\n        return AVLNode(val)\n    if val < node.val:\n        node.left = insert(node.left, val)\n    else:\n        node.right = insert(node.right, val)\n\n    update_height(node)\n    bf = balance_factor(node)\n\n    # LL case\n    if bf > 1 and val < node.left.val:\n        return rotate_right(node)\n    # RR case\n    if bf < -1 and val > node.right.val:\n        return rotate_left(node)\n    # LR case\n    if bf > 1 and val > node.left.val:\n        node.left = rotate_left(node.left)\n        return rotate_right(node)\n    # RL case\n    if bf < -1 and val < node.right.val:\n        node.right = rotate_right(node.right)\n        return rotate_left(node)\n\n    return node"},
            {"type": "resource_link", "label": "\U0001F4D6 Visualize AVL rotations interactively", "url": "https://www.cs.usfca.edu/~galles/visualization/AVLtree.html"},
            {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Red-Black Tree", "url": "https://www.geeksforgeeks.org/introduction-to-red-black-tree/"}
        ]
    },
    {
        "title": "B-Trees & Database Indexing",
        "difficulty": "advanced",
        "content_blocks": [
            {"type": "heading", "level": 2, "value": "Why Databases Don't Use Binary Trees"},
            {"type": "text", "value": "A **B-Tree** generalizes a BST so each node can hold many keys and have many children (not just 2). This matters because disk reads are orders of magnitude slower than memory access -- a binary tree over a million records needs ~20 disk seeks to find a value, while a B-Tree with a branching factor of a few hundred needs only 2-3, because each disk read pulls in an entire node's worth of keys at once. This is exactly why MySQL, PostgreSQL, and most filesystems use B-Trees (or the leaf-linked variant, B+ Trees) for indexing."},
            {"type": "list", "ordered": False, "items": [
                "**Order (branching factor) m** -- each node holds up to `m-1` keys and up to `m` children",
                "**All leaves at the same depth** -- unlike a BST, a B-Tree stays perfectly balanced by construction, not by rebalancing after the fact",
                "**Search / Insert / Delete** -- `O(log n)`, but with a much smaller constant than a binary tree due to the high branching factor",
                "**B+ Tree variant** -- keys are duplicated in leaf nodes and linked together, making range queries (`WHERE age BETWEEN 20 AND 30`) fast sequential scans"
            ]},
            {"type": "callout", "kind": "info", "title": "The real-world reason this matters", "value": "This is one of the few DSA topics that maps directly onto a system-design interview question: *'why does an index speed up a SQL query?'* -- the honest answer is almost always 'because it's a B+ Tree, and traversing it needs far fewer disk reads than a full table scan.'"},
            {"type": "code", "language": "python", "value": "# Simplified B-Tree node insert (order-based, conceptual implementation)\nclass BTreeNode:\n    def __init__(self, leaf=True):\n        self.keys = []\n        self.children = []\n        self.leaf = leaf\n\nclass BTree:\n    def __init__(self, order=3):\n        self.root = BTreeNode()\n        self.order = order  # max children per node\n\n    def insert(self, key):\n        root = self.root\n        if len(root.keys) == self.order - 1:\n            new_root = BTreeNode(leaf=False)\n            new_root.children.append(root)\n            self._split_child(new_root, 0)\n            self.root = new_root\n        self._insert_non_full(self.root, key)\n\n    def _insert_non_full(self, node, key):\n        i = len(node.keys) - 1\n        if node.leaf:\n            node.keys.append(None)\n            while i >= 0 and key < node.keys[i]:\n                node.keys[i + 1] = node.keys[i]\n                i -= 1\n            node.keys[i + 1] = key\n        else:\n            while i >= 0 and key < node.keys[i]:\n                i -= 1\n            i += 1\n            if len(node.children[i].keys) == self.order - 1:\n                self._split_child(node, i)\n                if key > node.keys[i]:\n                    i += 1\n            self._insert_non_full(node.children[i], key)\n\n    def _split_child(self, parent, i):\n        order = self.order\n        child = parent.children[i]\n        mid = (order - 1) // 2\n        new_node = BTreeNode(leaf=child.leaf)\n        new_node.keys = child.keys[mid + 1:]\n        parent.keys.insert(i, child.keys[mid])\n        parent.children.insert(i + 1, new_node)\n        child.keys = child.keys[:mid]\n        if not child.leaf:\n            new_node.children = child.children[mid + 1:]\n            child.children = child.children[:mid + 1]"},
            {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: B-Tree", "url": "https://www.geeksforgeeks.org/introduction-of-b-tree-2/"},
            {"type": "resource_link", "label": "\U0001F4D6 Free Textbook: Database Internals, Ch. 2-4 (B-Tree indexing)", "url": "https://www.databass.dev/"}
        ]
    }
]

NEW_PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-trees",
        "title": "Binary Tree Level Order Traversal",
        "difficulty": "medium",
        "description": "Given a binary tree represented as a space-separated level-order list (use -1 for null nodes), print its level-order traversal as space-separated values, one level per line... For this simplified version, given a space-separated list of integers representing a complete binary tree's array form (index i's children are at 2i+1, 2i+2), print the level-order traversal (i.e. just the input, since it is already level order) space-separated.",
        "starter_code": "def level_order(nums):\n    # nums is already in level-order array form -- filter out any -1 (null) markers\n    return [n for n in nums if n != -1]\n\nimport sys\nnums = list(map(int, sys.stdin.readline().split()))\nprint(' '.join(map(str, level_order(nums))))",
        "test_cases": [
            {"input": "3 9 20 -1 -1 15 7", "expected_output": "3 9 20 15 7"},
            {"input": "1", "expected_output": "1"},
            {"input": "1 2 3", "expected_output": "1 2 3"}
        ]
    },
    {
        "topic_slug": "dsa-trees",
        "title": "Validate BST",
        "difficulty": "medium",
        "description": "Given a space-separated in-order traversal of a binary tree, determine if it could represent a valid Binary Search Tree (i.e. the sequence is strictly increasing). Print 'true' or 'false'.",
        "starter_code": "def is_valid_bst_inorder(values):\n    return all(values[i] < values[i+1] for i in range(len(values) - 1))\n\nimport sys\nvals = list(map(int, sys.stdin.readline().split()))\nprint(str(is_valid_bst_inorder(vals)).lower())",
        "test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "true"},
            {"input": "5 3 1", "expected_output": "false"},
            {"input": "1 1 2", "expected_output": "false"}
        ]
    }
]

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    doc = await db.topics.find_one({"slug": "dsa-trees"})
    if not doc:
        print("ERROR -- dsa-trees topic not found")
        return

    existing_titles = [s.get("title") for s in doc.get("subtopics", [])]
    print("Existing subtopics:", existing_titles)

    for sub in doc["subtopics"]:
        if "difficulty" not in sub or sub.get("difficulty") is None:
            sub["difficulty"] = "beginner"

    traversal_sub = NEW_SUBTOPICS[0]
    avl_sub = NEW_SUBTOPICS[1]
    btree_sub = NEW_SUBTOPICS[2]

    new_subtopics = [traversal_sub] + doc["subtopics"] + [avl_sub, btree_sub]
    doc["subtopics"] = new_subtopics

    await db.topics.replace_one({"_id": doc["_id"]}, doc)
    print("Updated dsa-trees -- now has", len(new_subtopics), "subtopics")

    for problem in NEW_PRACTICE_PROBLEMS:
        existing_p = await db.practice_problems.find_one({"topic_slug": problem["topic_slug"], "title": problem["title"]})
        if existing_p:
            print("SKIP -- problem already exists:", problem["title"])
        else:
            await db.practice_problems.insert_one(problem)
            print("Inserted problem:", problem["title"])

asyncio.run(main())
