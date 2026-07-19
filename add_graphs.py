import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TOPIC = {
    "domain_slug": "dsa",
    "slug": "dsa-graphs",
    "title": "Graphs",
    "difficulty": "advanced",
    "content_blocks": [],
    "subtopics": [
        {
            "title": "Graph Representations & BFS/DFS Traversal",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Modeling Networks and Relationships"},
                {"type": "text", "value": "A **graph** is a set of nodes (vertices) connected by edges -- more general than a tree, since graphs can have cycles and multiple paths between two nodes. There are two standard ways to store one: an **adjacency list** (a dict mapping each node to its neighbors, space-efficient for sparse graphs) and an **adjacency matrix** (an n x n grid of 0/1s, fast edge lookups but wasteful for sparse graphs)."},
                {"type": "list", "ordered": False, "items": [
                    "**Adjacency List** -- `O(V + E)` space, `O(degree)` to list a node's neighbors -- the default choice for most problems",
                    "**Adjacency Matrix** -- `O(V^2)` space, `O(1)` to check if an edge exists -- better when the graph is dense or you need fast edge lookups",
                    "**BFS (queue-based)** -- explores level by level, finds shortest path in an *unweighted* graph, `O(V + E)`",
                    "**DFS (stack/recursion-based)** -- explores as deep as possible before backtracking, natural for cycle detection and topological sort, `O(V + E)`"
                ]},
                {"type": "callout", "kind": "tip", "title": "BFS vs DFS -- when to use which", "value": "Use **BFS** whenever the question involves 'shortest path' or 'fewest steps' in an unweighted graph. Use **DFS** for exhaustive exploration -- detecting cycles, topological sorting, or when you need to explore every path (e.g. counting islands)."},
                {"type": "code", "language": "python", "value": "from collections import deque, defaultdict\n\ndef build_graph(edges):\n    graph = defaultdict(list)\n    for u, v in edges:\n        graph[u].append(v)\n        graph[v].append(u)  # undirected\n    return graph\n\ndef bfs(graph, start):\n    visited = {start}\n    order = []\n    q = deque([start])\n    while q:\n        node = q.popleft()\n        order.append(node)\n        for neighbor in graph[node]:\n            if neighbor not in visited:\n                visited.add(neighbor)\n                q.append(neighbor)\n    return order\n\ndef dfs(graph, start, visited=None, order=None):\n    if visited is None:\n        visited, order = set(), []\n    visited.add(start)\n    order.append(start)\n    for neighbor in graph[start]:\n        if neighbor not in visited:\n            dfs(graph, neighbor, visited, order)\n    return order"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Graph Data Structure and Algorithms", "url": "https://www.geeksforgeeks.org/graph-data-structure-and-algorithms/"}
            ]
        },
        {
            "title": "Shortest Path: Dijkstra's Algorithm",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Finding the Cheapest Route in a Weighted Graph"},
                {"type": "text", "value": "BFS finds the shortest path by *edge count*, but real-world graphs often have weighted edges (distance, cost, time). **Dijkstra's algorithm** finds the shortest path from a source to every other node by always expanding the closest unvisited node next, using a min-heap as a priority queue -- greedily locking in the shortest known distance at each step."},
                {"type": "list", "ordered": False, "items": [
                    "**Time complexity (heap-based)** -- `O((V + E) log V)`",
                    "**Requirement** -- all edge weights must be non-negative; Dijkstra's greedy choice breaks down with negative weights",
                    "**Bellman-Ford** -- handles negative weights (and detects negative cycles), but is slower at `O(V * E)`",
                    "**A\\*** -- Dijkstra plus a heuristic function, used when you have extra knowledge about the goal's direction (e.g. pathfinding on a grid)"
                ]},
                {"type": "callout", "kind": "warning", "title": "Why negative weights break Dijkstra", "value": "Dijkstra assumes that once a node is popped from the heap with its shortest distance, that distance can never improve later. A negative edge can violate this -- a longer path taken first could later become shorter via a negative edge, but Dijkstra has already 'locked in' the wrong answer and won't revisit it."},
                {"type": "code", "language": "python", "value": "import heapq\nfrom collections import defaultdict\n\ndef dijkstra(graph, start):\n    # graph: dict of node -> list of (neighbor, weight)\n    dist = defaultdict(lambda: float('inf'))\n    dist[start] = 0\n    heap = [(0, start)]\n\n    while heap:\n        d, node = heapq.heappop(heap)\n        if d > dist[node]:\n            continue  # stale entry, skip\n        for neighbor, weight in graph[node]:\n            new_dist = d + weight\n            if new_dist < dist[neighbor]:\n                dist[neighbor] = new_dist\n                heapq.heappush(heap, (new_dist, neighbor))\n\n    return dict(dist)\n\ngraph = defaultdict(list)\ngraph['A'] = [('B', 4), ('C', 1)]\ngraph['C'] = [('B', 2), ('D', 5)]\ngraph['B'] = [('D', 1)]\nprint(dijkstra(graph, 'A'))  # {'A': 0, 'B': 3, 'C': 1, 'D': 4}"},
                {"type": "resource_link", "label": "\U0001F4D6 Visualize Dijkstra's algorithm interactively", "url": "https://www.cs.usfca.edu/~galles/visualization/Dijkstra.html"}
            ]
        },
        {
            "title": "Minimum Spanning Tree: Kruskal's & Prim's",
            "difficulty": "advanced",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Connecting Every Node for the Least Total Cost"},
                {"type": "text", "value": "A **Minimum Spanning Tree (MST)** connects all nodes in a weighted graph using the minimum possible total edge weight, with no cycles. **Kruskal's algorithm** sorts all edges by weight and greedily adds each one unless it would form a cycle (checked efficiently with **Union-Find**). **Prim's algorithm** instead grows a single tree outward, always adding the cheapest edge that connects a new node -- conceptually similar to Dijkstra but minimizing edge weight instead of path distance."},
                {"type": "list", "ordered": False, "items": [
                    "**Kruskal's** -- `O(E log E)` for sorting edges, best when the graph is sparse",
                    "**Prim's** -- `O(E log V)` with a heap, best when the graph is dense",
                    "**Union-Find (Disjoint Set Union)** -- with path compression and union by rank, near-`O(1)` amortized per operation -- this is the enabling data structure behind Kruskal's cycle detection",
                    "**Real-world use** -- network design (minimum cable to connect all cities), clustering algorithms"
                ]},
                {"type": "callout", "kind": "info", "title": "Why Union-Find matters here", "value": "Naively checking 'would this edge create a cycle?' by running a DFS/BFS on every candidate edge would be `O(V)` per check, making Kruskal's `O(E * V)` overall. Union-Find turns that check into a near-constant-time operation, which is what makes Kruskal's practically `O(E log E)`."},
                {"type": "code", "language": "python", "value": "class UnionFind:\n    def __init__(self, n):\n        self.parent = list(range(n))\n        self.rank = [0] * n\n\n    def find(self, x):\n        if self.parent[x] != x:\n            self.parent[x] = self.find(self.parent[x])  # path compression\n        return self.parent[x]\n\n    def union(self, x, y):\n        px, py = self.find(x), self.find(y)\n        if px == py:\n            return False  # already connected -- would form a cycle\n        if self.rank[px] < self.rank[py]:\n            px, py = py, px\n        self.parent[py] = px\n        if self.rank[px] == self.rank[py]:\n            self.rank[px] += 1\n        return True\n\ndef kruskal(n, edges):\n    # edges: list of (weight, u, v)\n    edges = sorted(edges)\n    uf = UnionFind(n)\n    mst_weight = 0\n    for weight, u, v in edges:\n        if uf.union(u, v):\n            mst_weight += weight\n    return mst_weight\n\nedges = [(1, 0, 1), (4, 0, 2), (2, 1, 2), (5, 1, 3), (3, 2, 3)]\nprint(kruskal(4, edges))  # 6"},
                {"type": "resource_link", "label": "\U0001F4C4 GeeksforGeeks: Kruskal's Minimum Spanning Tree Algorithm", "url": "https://www.geeksforgeeks.org/kruskals-minimum-spanning-tree-algorithm-greedy-algo-2/"}
            ]
        }
    ]
}

PRACTICE_PROBLEMS = [
    {
        "topic_slug": "dsa-graphs",
        "title": "Number of Connected Components",
        "difficulty": "medium",
        "description": "Given n nodes (0 to n-1) and a list of edges, find the number of connected components. First line: n. Second line: space-separated pairs flattened (e.g. '0 1 2 3' means edges (0,1) and (2,3)). If no edges, second line is empty.",
        "starter_code": "def count_components(n, edges):\n    parent = list(range(n))\n    def find(x):\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n    def union(x, y):\n        px, py = find(x), find(y)\n        if px != py:\n            parent[px] = py\n    for u, v in edges:\n        union(u, v)\n    return len(set(find(i) for i in range(n)))\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nn = int(lines[0])\nparts = list(map(int, lines[1].split())) if len(lines) > 1 and lines[1].strip() else []\nedges = [(parts[i], parts[i+1]) for i in range(0, len(parts), 2)]\nprint(count_components(n, edges))",
        "test_cases": [
            {"input": "5\n0 1 1 2", "expected_output": "3"},
            {"input": "4\n0 1 2 3", "expected_output": "2"},
            {"input": "3\n", "expected_output": "3"}
        ]
    },
    {
        "topic_slug": "dsa-graphs",
        "title": "BFS Shortest Path Length",
        "difficulty": "medium",
        "description": "Given n nodes, a list of undirected edges, a start node, and an end node, find the shortest path length (number of edges) using BFS. Print -1 if unreachable. First line: n. Second line: flattened edge pairs. Third line: start end.",
        "starter_code": "from collections import deque, defaultdict\n\ndef shortest_path(n, edges, start, end):\n    graph = defaultdict(list)\n    for u, v in edges:\n        graph[u].append(v)\n        graph[v].append(u)\n    visited = {start}\n    q = deque([(start, 0)])\n    while q:\n        node, dist = q.popleft()\n        if node == end:\n            return dist\n        for neighbor in graph[node]:\n            if neighbor not in visited:\n                visited.add(neighbor)\n                q.append((neighbor, dist + 1))\n    return -1\n\nimport sys\nlines = sys.stdin.read().split(chr(10))\nn = int(lines[0])\nparts = list(map(int, lines[1].split())) if lines[1].strip() else []\nedges = [(parts[i], parts[i+1]) for i in range(0, len(parts), 2)]\nstart, end = map(int, lines[2].split())\nprint(shortest_path(n, edges, start, end))",
        "test_cases": [
            {"input": "5\n0 1 1 2 2 3\n0 3", "expected_output": "3"},
            {"input": "3\n0 1\n0 2", "expected_output": "-1"},
            {"input": "2\n0 1\n0 1", "expected_output": "1"}
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
