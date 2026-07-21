import asyncio
import sys
import os
sys.path.insert(0, r"c:\Users\navaneeth\Ai-placement-mentor")
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

TOPICS = [
    {
        "slug": "intro-python",
        "title": "Introduction to Python, Syntax & Data Types",
        "domain_slug": "python",
        "difficulty": "beginner",
        "subtopics": [
            {
                "title": "Python Overview & Execution Model",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Python Execution & Compilation"},
                    {"type": "text", "value": "Python is an interpreted, high-level, dynamically typed language. When you run a Python script, the source code is first compiled into intermediate **bytecode** (`.pyc` files), which is then executed by the Python Virtual Machine (PVM). Understanding this compilation-execution phase is key to understanding Python's startup time and runtime performance."},
                    {"type": "diagram", "title": "Python Execution Model", "value": "flowchart LR\n    Source[.py Source] --> Compiler[Compiler]\n    Compiler --> Bytecode[.pyc Bytecode]\n    Bytecode --> PVM[Python Virtual Machine]\n    PVM --> Output[Runtime Execution]"},
                    {"type": "callout", "kind": "info", "title": "Execution Reality", "value": "Although Python is called an 'interpreted' language, compilation to bytecode happens transparently behind the scenes. This is why you see `__pycache__` folders in your projects."},
                    {"type": "knowledge_check", "question": "What is the primary role of the Python Virtual Machine (PVM)?", "options": [
                        "To compile .py source files directly to binary machine code.",
                        "To execute the compiled bytecode instructions line-by-line.",
                        "To manage project dependencies and virtual environments."
                    ], "correct_index": 1, "explanation": "The Python compiler converts source code into bytecode, and then the PVM executes this bytecode."}
                ]
            },
            {
                "title": "Variables, Dynamic Typing & References",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Variables are References, Not Boxes"},
                    {"type": "text", "value": "In Python, variables are references to objects stored in memory. When you assign `x = 5`, Python creates an integer object `5` and binds the label `x` to it. If you assign `y = x`, `y` is bound to the exact same object. This is called **binding/reference assignment**."},
                    {"type": "code", "language": "python", "value": "x = [1, 2, 3]\ny = x\ny.append(4)\nprint(x)  # Output: [1, 2, 3, 4] - both point to the same list!"},
                    {"type": "callout", "kind": "warning", "title": "Common Gotcha", "value": "Variables of mutable types (like lists, dicts, sets) show this shared-reference behavior, while immutable types (int, float, str, tuple) simulate values by returning a new object on modifications."},
                    {"type": "knowledge_check", "question": "What happens when you run `a = 10; b = a; a = 20`?", "options": [
                        "Both a and b will equal 20 because b points to a.",
                        "a will equal 20, and b will equal 10 because integers are immutable.",
                        "A syntax error is thrown."
                    ], "correct_index": 1, "explanation": "Assigning `a = 20` rebinds the variable `a` to a new integer object `20`. The reference `b` remains bound to the original integer object `10`."}
                ]
            },
            {
                "title": "Built-in Data Types & Mutability",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Mutability and Object Identity"},
                    {"type": "text", "value": "Python objects are categorized as either **mutable** (can be changed in-place) or **immutable** (cannot be changed after creation). This distinction governs hashing, dictionary keys, and function defaults."},
                    {"type": "list", "ordered": False, "items": [
                        "**Immutable Types**: `int`, `float`, `str`, `tuple`, `bool`, `bytes`, `frozenset`",
                        "**Mutable Types**: `list`, `dict`, `set`, `bytearray`"
                    ]},
                    {"type": "code", "language": "python", "value": "# Check object identity using id()\na = 'hello'\nb = 'hello'\nprint(a is b)  # True (string interning)\n\nx = (1, 2)\n# x[0] = 3  # TypeError: 'tuple' object does not support item assignment"},
                    {"type": "callout", "kind": "important", "title": "Interview Lens", "value": "Only immutable types can be hashed. Because dictionary keys and set elements require a stable hash value to maintain hash-table slots, mutable objects (like lists or dicts) cannot be dictionary keys or set members."},
                    {"type": "knowledge_check", "question": "Which of the following can be used as a key in a Python dictionary?", "options": [
                        "A list of integers: `[1, 2]`",
                        "A tuple containing a list: `(1, [2, 3])`",
                        "A tuple of immutable objects: `(1, 'abc')`"
                    ], "correct_index": 2, "explanation": "A tuple is hashable only if all of its elements are hashable. A list is mutable and thus unhashable, making option 2 unhashable as well."}
                ]
            }
        ]
    },
    {
        "slug": "python-control-flow-and-functions",
        "title": "Control Flow & Functions",
        "domain_slug": "python",
        "difficulty": "beginner",
        "subtopics": [
            {
                "title": "Conditionals, Loops & Iterators",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Python Loops and Control Structures"},
                    {"type": "text", "value": "Python provides `if/elif/else` for branching and `for` / `while` loops for iteration. A unique feature of Python loops is the `else` clause: the `else` block executes only if the loop completes normally without hitting a `break` statement."},
                    {"type": "code", "language": "python", "value": "for num in [2, 4, 6]:\n    if num % 2 != 0:\n        break\nelse:\n    print('All numbers were even!')  # Executes because break was not hit"},
                    {"type": "callout", "kind": "tip", "title": "For-Else Use Case", "value": "The `else` clause is useful for search loops where you want to execute code only if no match was found."},
                    {"type": "knowledge_check", "question": "Under what condition does a `while...else` loop's `else` block run?", "options": [
                        "When the while condition becomes false.",
                        "When the loop is terminated by a break statement.",
                        "Only if the loop body never runs."
                    ], "correct_index": 0, "explanation": "The else block executes when the loop condition evaluates to false. If a break statement exits the loop, the else block is bypassed."}
                ]
            },
            {
                "title": "Function Arguments, Passing & Scope",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Argument Passing: Call-by-Object"},
                    {"type": "text", "value": "Python uses **call-by-sharing** (or call-by-object-reference). You pass a reference to the same object. If the object is mutable, modifications inside the function affect the caller; if it is immutable, rebinding inside the function does not change the caller's reference."},
                    {"type": "code", "language": "python", "value": "def append_element(lst):\n    lst.append(99)  # changes in-place\n\ndef rebind_val(x):\n    x = 10  # rebinds local label x\n\nmy_list = [1, 2]\nappend_element(my_list)\nprint(my_list)  # Output: [1, 2, 99]\n\nval = 5\nrebind_val(val)\nprint(val)  # Output: 5"},
                    {"type": "callout", "kind": "warning", "title": "Mutable Default Arguments Gotcha", "value": "Default arguments are evaluated once when the function is defined. If you use a mutable default like `def func(x=[])`, the same list object is shared across all function calls that omit the parameter."},
                    {"type": "knowledge_check", "question": "What is the standard way to avoid mutable default arguments pitfalls?", "options": [
                        "Use `def func(x=list())`.",
                        "Use `def func(x=None)` and initialize inside: `if x is None: x = []`.",
                        "Always cast the argument to list inside the function."
                    ], "correct_index": 1, "explanation": "Using `None` as a sentinel and instantiating the list inside ensures a new list object is created on each call."}
                ]
            },
            {
                "title": "LEGB Scope & Closures",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Variable Scope & Resolution"},
                    {"type": "text", "value": "Python resolves variable names using the **LEGB rule**: Local, Enclosing (nonlocal), Global, and Built-in. If a name is not found in these scopes, a `NameError` is raised."},
                    {"type": "code", "language": "python", "value": "x = 'global'\ndef outer():\n    x = 'enclosing'\n    def inner():\n        nonlocal x  # references outer's x\n        x = 'modified enclosing'\n    inner()\n    print(x)\nouter()  # Output: modified enclosing"},
                    {"type": "callout", "kind": "important", "title": "Closures", "value": "A closure is a nested function that retains access to variables from its enclosing scope even after the outer function has finished executing."},
                    {"type": "knowledge_check", "question": "What does the `nonlocal` keyword do in Python?", "options": [
                        "Declares a variable in the global module scope.",
                        "Declares that a variable belongs to the parent/enclosing function scope.",
                        "Allows variables to be accessed across different threads."
                    ], "correct_index": 1, "explanation": "The nonlocal keyword is used in nested functions to refer to variables defined in the nearest enclosing outer function scope."}
                ]
            }
        ]
    },
    {
        "slug": "python-core-data-structures",
        "title": "Core Data Structures (Lists, Dicts, Sets, Tuples)",
        "domain_slug": "python",
        "difficulty": "beginner",
        "subtopics": [
            {
                "title": "Lists & Tuples: Arrays vs. Records",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Under the Hood: Lists vs. Tuples"},
                    {"type": "text", "value": "In Python, a **list** is a dynamic array of object references. It over-allocates memory to support amortized $O(1)$ appends. A **tuple** is a static array with fixed memory size, making it memory-efficient and read-only. Tuples are typically used as heterogeneous records, whereas lists are homogeneous collections."},
                    {"type": "code", "language": "python", "value": "import sys\na_list = [1, 2, 3]\na_tuple = (1, 2, 3)\nprint(sys.getsizeof(a_list))   # Larger (due to dynamic resizing buffer)\nprint(sys.getsizeof(a_tuple))  # Smaller"},
                    {"type": "callout", "kind": "info", "title": "Memory Layout", "value": "Because tuples are immutable, Python can allocate exact memory slots for them. Lists maintain a resize buffer to avoid costly reallocations on every append."},
                    {"type": "knowledge_check", "question": "What is the time complexity of appending to a Python list?", "options": [
                        "O(N) in the worst case, but amortized O(1).",
                        "Strictly O(1) always.",
                        "O(log N)."
                    ], "correct_index": 0, "explanation": "Appending is usually O(1), but when the list's pre-allocated buffer is full, Python must allocate a larger array and copy all references, taking O(N) time."}
                ]
            },
            {
                "title": "Dictionaries & Sets: Hash Tables in Python",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Hash Maps and Sets under the Hood"},
                    {"type": "text", "value": "Python dictionaries and sets are implemented as **hash tables**. Finding an element or checking membership takes $O(1)$ average time. Dictionaries require keys to be hashable (immutable) and since Python 3.6, they preserve insertion order using a split index/value array representation."},
                    {"type": "code", "language": "python", "value": "my_set = {1, 2, 3}\nprint(4 in my_set)  # O(1) membership test\n\n# Dynamic dict manipulation\ninfo = {'name': 'Alice', 'role': 'SDE'}\nprint(info.get('age', 25))  # Safe access with default value"},
                    {"type": "callout", "kind": "important", "title": "Insertion Order", "value": "Although dicts preserve insertion order, they remain hash tables and do not allow indexed access like lists. Reordering them must be done explicitly (e.g., using `collections.OrderedDict`)."},
                    {"type": "knowledge_check", "question": "Why is checking membership in a set (`val in my_set`) faster than in a list (`val in my_list`)?", "options": [
                        "Sets are sorted, allowing binary search O(log N).",
                        "Sets use a hash table allowing O(1) lookup on average.",
                        "Sets use less memory than lists."
                    ], "correct_index": 1, "explanation": "Sets are built on hash tables, so lookup is O(1) average time, while lists require a linear scan of O(N) time."}
                ]
            },
            {
                "title": "Comprehensions & Generator Expressions",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Writing Idiomatic Comprehensions"},
                    {"type": "text", "value": "Python supports comprehensions for lists, dicts, and sets. When wrapped in parentheses, the expression becomes a **generator expression** which produces values lazily, conserving memory when dealing with large datasets."},
                    {"type": "code", "language": "python", "value": "squares = [x**2 for x in range(10)]  # List comprehension\neven_set = {x for x in range(20) if x % 2 == 0}  # Set comprehension\n\n# Generator expression: does not load items in memory\nsquare_gen = (x**2 for x in range(1000000))\nprint(next(square_gen))  # 0\nprint(next(square_gen))  # 1"},
                    {"type": "callout", "kind": "tip", "title": "Memory Optimization", "value": "Always prefer generator expressions over list comprehensions if you only need to iterate over the items once (e.g., in `sum(x for x in data)`)."},
                    {"type": "knowledge_check", "question": "What is the key benefit of a generator expression over a list comprehension?", "options": [
                        "It executes faster in all cases.",
                        "It returns a tuple instead of a list.",
                        "It evaluates values lazily, consuming minimal memory."
                    ], "correct_index": 2, "explanation": "Generators stream items one at a time on demand instead of allocating the entire list in memory at once."}
                ]
            }
        ]
    },
    {
        "slug": "python-object-oriented-programming",
        "title": "Object-Oriented Programming in Python",
        "domain_slug": "python",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Classes, MRO & Multiple Inheritance",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Method Resolution Order (MRO)"},
                    {"type": "text", "value": "Python supports multiple inheritance. To resolve which method to call in complex inheritance hierarchies, Python uses the **C3 Linearization** algorithm to build the Method Resolution Order (MRO). You can view the resolution path using the `__mro__` attribute or `.mro()` method."},
                    {"type": "code", "language": "python", "value": "class A:\n    def greet(self):\n        return 'A'\nclass B(A):\n    def greet(self):\n        return 'B'\nclass C(A):\n    def greet(self):\n        return 'C'\nclass D(B, C):\n    pass\n\nprint(D.mro())\n# Output: [D, B, C, A, object]\nprint(D().greet())  # Output: B"},
                    {"type": "callout", "kind": "important", "title": "Super()", "value": "The `super()` function calls the next method in the MRO, not necessarily the parent class. In multiple inheritance, this is crucial for cooperative method invocation."},
                    {"type": "knowledge_check", "question": "In Python multiple inheritance, what determines the search order for attributes and methods?", "options": [
                        "The order classes are declared in the module.",
                        "The Method Resolution Order (MRO) calculated using C3 Linearization.",
                        "Depth-First Search (DFS) without exception checks."
                    ], "correct_index": 1, "explanation": "Python calculates the Method Resolution Order (MRO) to handle cooperative multiple inheritance without cycles."}
                ]
            },
            {
                "title": "Special Dunder Methods",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Customizing Object Behavior"},
                    {"type": "text", "value": "Dunder (double underscore) methods allow user-defined classes to hook into Python's built-in operators and syntax. Implementing `__str__`, `__repr__`, `__len__`, or arithmetic operators makes objects feel native."},
                    {"type": "code", "language": "python", "value": "class Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n    \n    def __repr__(self):\n        return f'Point({self.x}, {self.y})'\n    \n    def __add__(self, other):\n        return Point(self.x + other.x, self.y + other.y)\n\np1 = Point(1, 2)\np2 = Point(3, 4)\nprint(p1 + p2)  # Output: Point(4, 6)"},
                    {"type": "callout", "kind": "tip", "title": "__str__ vs __repr__", "value": "`__repr__` should provide an unambiguous string representation (ideally valid Python code to recreate the object) for developers, whereas `__str__` is a user-friendly string."},
                    {"type": "knowledge_check", "question": "Which dunder method should you implement to make your custom objects usable with the `len()` function?", "options": [
                        "`__size__`",
                        "`__length__`",
                        "`__len__`"
                    ], "correct_index": 2, "explanation": "Implementing `__len__` on a class allows it to respond to the built-in `len()` function."}
                ]
            },
            {
                "title": "Decorators and Properties inside Classes",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Encapsulation: Getters, Setters & Static Methods"},
                    {"type": "text", "value": "Python does not have strict private access modifiers. It uses naming conventions (`_protected`, `__private` with name mangling) and the `@property` decorator to implement clean encapsulation without public getters and setters."},
                    {"type": "code", "language": "python", "value": "class Account:\n    def __init__(self, balance):\n        self._balance = balance\n\n    @property\n    def balance(self):\n        return self._balance\n\n    @balance.setter\n    def balance(self, value):\n        if value < 0:\n            raise ValueError('Balance cannot be negative')\n        self._balance = value\n\nacc = Account(100)\nacc.balance = 150  # Uses setter\nprint(acc.balance)  # Uses getter"},
                    {"type": "callout", "kind": "info", "title": "Class vs Static Methods", "value": "`@classmethod` receives the class object `cls` as the first argument, while `@staticmethod` receives no special first argument and acts as a plain function grouped inside the class namespace."},
                    {"type": "knowledge_check", "question": "What is Python's name mangling mechanism?", "options": [
                        "Prefixing a variable with an underscore (`_var`) to prevent editing.",
                        "Prefixing an attribute with two leading underscores (`__var`) to rewrite its name as `_ClassName__var` to prevent naming collisions.",
                        "Encrypting variable names at runtime."
                    ], "correct_index": 1, "explanation": "Double leading underscores activate name mangling, which changes the name of the attribute internally to prevent child classes from accidentally overriding it."}
                ]
            }
        ]
    },
    {
        "slug": "python-file-and-exception-handling",
        "title": "File Handling & Exception Handling",
        "domain_slug": "python",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "File I/O & Context Managers",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Safe Resource Management"},
                    {"type": "text", "value": "When interacting with external resources (like files, sockets, database connections), it is crucial to release them. The `with` statement uses **context managers** to guarantee that resources are cleaned up even if exceptions occur during execution."},
                    {"type": "code", "language": "python", "value": "# Using context manager to open file safely\nwith open('sample.txt', 'w') as f:\n    f.write('Hello, placement platform!')\n# File is automatically closed here, even if an error is raised inside"},
                    {"type": "callout", "kind": "important", "title": "The Context Manager Protocol", "value": "Any class implementing `__enter__` and `__exit__` dunder methods can be used in a `with` statement. You can also build context managers easily using the `@contextmanager` decorator from `contextlib`."},
                    {"type": "knowledge_check", "question": "Why is the `with` statement preferred over manually opening and closing files?", "options": [
                        "It reads the file faster.",
                        "It guarantees the file is closed even if an exception occurs inside the block.",
                        "It automatically encrypts the file."
                    ], "correct_index": 1, "explanation": "The context manager's __exit__ method is guaranteed to execute, closing files/releasing resources, regardless of exception states."}
                ]
            },
            {
                "title": "Exception Hierarchy & Custom Exceptions",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Writing Robust try/except Blocks"},
                    {"type": "text", "value": "Python exceptions are organized in an inheritance hierarchy. The base exception is `BaseException`, but user exceptions should inherit from `Exception`. Always catch specific exceptions rather than a generic `except:` statement, which can accidentally swallow system interrupts like `KeyboardInterrupt`."},
                    {"type": "code", "language": "python", "value": "class InsufficientFundsError(Exception):\n    \"\"\"Custom business logic exception\"\"\"\n    pass\n\ntry:\n    balance = 50\n    if balance < 100:\n        raise InsufficientFundsError('Withdrawal exceeds balance')\nexcept InsufficientFundsError as e:\n    print(f'Transaction Failed: {e}')\nfinally:\n    print('Cleaning up database connection...')"},
                    {"type": "callout", "kind": "tip", "title": "Except Else Clause", "value": "You can include an `else` block after `except`. The `else` block executes only if the code in the `try` block did NOT throw any exceptions."},
                    {"type": "knowledge_check", "question": "What is the purpose of the `finally` block in an exception handling block?", "options": [
                        "It runs only if no exception was raised.",
                        "It runs only if an exception was raised and caught.",
                        "It is guaranteed to run regardless of whether an exception was raised or caught."
                    ], "correct_index": 2, "explanation": "The `finally` block is executed under all circumstances (even after return statements in try/except) to perform cleanup actions."}
                ]
            }
        ]
    },
    {
        "slug": "python-iterators-generators-decorators",
        "title": "Iterators, Generators & Decorators",
        "domain_slug": "python",
        "difficulty": "advanced",
        "subtopics": [
            {
                "title": "The Iterator Protocol",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Iterables vs. Iterators"},
                    {"type": "text", "value": "An **iterable** is any object that can return its elements one by one (e.g. list, string). It must implement `__iter__` to return an **iterator**. An **iterator** is the stateful stream object that actually returns elements via the `__next__` method and raises `StopIteration` when exhausted."},
                    {"type": "code", "language": "python", "value": "class Counter:\n    def __init__(self, limit):\n        self.limit = limit\n        self.val = 0\n    \n    def __iter__(self):\n        return self\n    \n    def __next__(self):\n        if self.val < self.limit:\n            self.val += 1\n            return self.val\n        raise StopIteration\n\nfor x in Counter(3):\n    print(x)  # prints 1, 2, 3"},
                    {"type": "callout", "kind": "info", "title": "Under the Hood", "value": "A standard `for` loop calls `iter(obj)` to get an iterator, then repeatedly calls `next(iterator)` inside a try/except block that catches `StopIteration`."},
                    {"type": "knowledge_check", "question": "Which two methods must a class implement to conform to the Iterator Protocol?", "options": [
                        "`__iter__` and `__next__`",
                        "`__get__` and `__set__`",
                        "`__enter__` and `__exit__`"
                    ], "correct_index": 0, "explanation": "An iterator must have `__iter__` (returning self) and `__next__` (returning the next item or raising StopIteration)."}
                ]
            },
            {
                "title": "Generators & Yield",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Suspended State Execution"},
                    {"type": "text", "value": "Generators are functions that use the `yield` keyword. Unlike standard functions that return a value and terminate, generators yield a value and temporarily suspend execution, saving their execution state, local variables, and instruction pointer. They resume when `next()` is called again."},
                    {"type": "code", "language": "python", "value": "def fibonacci(limit):\n    a, b = 0, 1\n    for _ in range(limit):\n        yield a\n        a, b = b, a + b\n\nprint(list(fibonacci(5)))  # Output: [0, 1, 1, 2, 3]"},
                    {"type": "callout", "kind": "tip", "title": "Memory Efficiency", "value": "Generators allow processing infinite streams or large logs without ever loading the whole dataset into RAM, allowing $O(1)$ memory consumption."},
                    {"type": "knowledge_check", "question": "What happens to the local variables of a generator function when a `yield` statement is hit?", "options": [
                        "They are cleared from memory.",
                        "Their state is frozen/suspended and kept in memory until the generator is resumed or deleted.",
                        "They are written to a temporary cache file."
                    ], "correct_index": 1, "explanation": "The generator pauses execution and retains all of its local frame data in memory, resuming exactly where it left off on the next invocation."}
                ]
            },
            {
                "title": "Closures & Function Decorators",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Wrapping Functions in Python"},
                    {"type": "text", "value": "A **decorator** is a function that takes another function as an argument, extends its behavior without modifying it directly, and returns a new function. This is an implementation of the structural Design Pattern *Decorator*."},
                    {"type": "code", "language": "python", "value": "import time\n\ndef timer_decorator(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} took {time.time() - start:.6f}s')\n        return result\n    return wrapper\n\n@timer_decorator\ndef compute():\n    return sum(x for x in range(1000000))\n\ncompute()"},
                    {"type": "callout", "kind": "important", "title": "@functools.wraps", "value": "Always use `@functools.wraps(func)` on your wrapper function. This preserves the original name, docstring, and metadata of the decorated function, preventing debug traceback confusion."},
                    {"type": "knowledge_check", "question": "What is the primary role of a decorator in Python?", "options": [
                        "To compile a function to faster bytecode.",
                        "To wrap a function and dynamically modify or extend its behavior without changing its source code.",
                        "To force type checking on arguments."
                    ], "correct_index": 1, "explanation": "Decorators provide a clean syntax to intercept, modify, or log calls to functions or classes."}
                ]
            }
        ]
    },
    {
        "slug": "python-modules-packages-environments",
        "title": "Modules, Packages & Virtual Environments",
        "domain_slug": "python",
        "difficulty": "intermediate",
        "subtopics": [
            {
                "title": "Modules, Sys.path & Importing",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "How Python Resolves Imports"},
                    {"type": "text", "value": "A Python module is simply a `.py` file. A package is a directory containing modules (historically marked with `__init__.py`). When you run `import my_module`, Python searches for the module in directories listed in `sys.path`, starting with the script's directory, then standard libraries, and finally `site-packages`."},
                    {"type": "code", "language": "python", "value": "import sys\n# Print path search list\nfor path in sys.path[:3]:\n    print(path)"},
                    {"type": "callout", "kind": "warning", "title": "Circular Imports", "value": "If module A imports module B, and module B imports module A, it creates a circular dependency. This can lead to partial module loads and `AttributeError` at runtime. Resolve this by refactoring shared code into a third module or moving imports inside functions."},
                    {"type": "knowledge_check", "question": "Where does Python look for modules when an `import` is executed?", "options": [
                        "Only in the current directory.",
                        "In the directories listed in `sys.path`.",
                        "Online in the PyPI package repository."
                    ], "correct_index": 1, "explanation": "sys.path contains a list of directory strings (local, env, installation directories) that Python searches in order."}
                ]
            },
            {
                "title": "Virtual Environments & Package Managers",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Isolation using venv and pip"},
                    {"type": "text", "value": "A **virtual environment** (`venv`) is an isolated Python directory containing its own Python interpreter, standard binaries, and site-packages. This isolates dependency lists across different projects on the same machine, preventing global package conflicts."},
                    {"type": "code", "language": "python", "value": "# Shell commands to manage environments\n# python -m venv myenv\n# source myenv/bin/activate (Linux/Mac) or myenv\\Scripts\\activate (Windows)\n# pip install -r requirements.txt"},
                    {"type": "callout", "kind": "info", "title": "Pip Freeze", "value": "Running `pip freeze > requirements.txt` dumps the exact versions of installed packages to ensure reproducible builds on other systems or deployments."},
                    {"type": "knowledge_check", "question": "Why should you always develop inside a Python virtual environment?", "options": [
                        "It makes Python code compile to faster executables.",
                        "It isolates dependencies for each project, avoiding version conflicts between global libraries.",
                        "It acts as a secure firewall for your files."
                    ], "correct_index": 1, "explanation": "Virtual environments isolate package installations, ensuring different project requirements (e.g. Django 3 vs Django 4) do not conflict."}
                ]
            }
        ]
    },
    {
        "slug": "python-concurrency",
        "title": "Concurrency: Threading, Multiprocessing & Asyncio",
        "domain_slug": "python",
        "difficulty": "advanced",
        "subtopics": [
            {
                "title": "The Global Interpreter Lock (GIL)",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Understanding the GIL Constraints"},
                    {"type": "text", "value": "CPython (the standard Python interpreter) uses the **Global Interpreter Lock (GIL)** to protect internal state. The GIL is a mutual exclusion lock that ensures only one native thread executes Python bytecode at any given moment. This makes multi-threaded Python programs single-threaded on multi-core systems for CPU-bound tasks."},
                    {"type": "diagram", "title": "GIL Execution Model", "value": "flowchart TD\n    subgraph Core1[CPU Core 1]\n        T1[Thread 1: Holds GIL]\n    end\n    subgraph Core2[CPU Core 2]\n        T2[Thread 2: Blocked / Waiting for GIL]\n    end\n    T1 -->|Releases GIL on I/O or timeslice| T2"},
                    {"type": "callout", "kind": "important", "title": "GIL Reality", "value": "The GIL does NOT block thread scheduling when threads run external C code (like NumPy vector math) or wait for network/disk I/O. Therefore, threading in Python is still highly effective for I/O-bound tasks."},
                    {"type": "knowledge_check", "question": "What is the main limitation of CPython's Global Interpreter Lock (GIL)?", "options": [
                        "It prevents multiple Python processes from running at the same time.",
                        "It limits Python code execution to a single core/thread at a time, making standard threads ineffective for CPU-bound tasks.",
                        "It prevents file reads and writes."
                    ], "correct_index": 1, "explanation": "The GIL limits bytecode execution to one thread, preventing multi-threaded programs from leveraging multiple CPU cores for CPU-heavy computation."}
                ]
            },
            {
                "title": "Threading vs. Multiprocessing",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Choosing the Right Concurrency Tool"},
                    {"type": "text", "value": "To achieve concurrency, Python provides two modules:\n1. **threading** -- threads share the same memory space. Low memory overhead, but bound by the GIL. Ideal for I/O-bound tasks (network requests, database calls).\n2. **multiprocessing** -- spins up separate operating system processes, each with its own memory space and interpreter instance. Bypasses the GIL entirely. Ideal for CPU-bound tasks (image processing, math simulations)."},
                    {"type": "code", "language": "python", "value": "import threading\nfrom multiprocessing import Process\n\ndef task():\n    print('Executing task...')\n\n# Multi-threading (I/O bound)\nt = threading.Thread(target=task)\nt.start()\nt.join()\n\n# Multi-processing (CPU bound)\np = Process(target=task)\np.start()\np.join()"},
                    {"type": "callout", "kind": "warning", "title": "IPC Cost", "value": "Because processes do not share memory, communicating between them requires Inter-Process Communication (IPC) mechanisms like `Queue` or `Pipe`, which incur serialization overhead."},
                    {"type": "knowledge_check", "question": "If you are building a tool to compute prime numbers up to 10 billion, which module should you use?", "options": [
                        "threading",
                        "multiprocessing",
                        "asyncio"
                    ], "correct_index": 1, "explanation": "Computing primes is a CPU-bound task. Only `multiprocessing` can bypass the GIL and utilize multiple CPU cores to speed up computation."}
                ]
            },
            {
                "title": "Cooperative Multitasking with Asyncio",
                "content_blocks": [
                    {"type": "heading", "level": 2, "value": "Event-Loop and Coroutines"},
                    {"type": "text", "value": "The **asyncio** module implements single-threaded concurrent code using **coroutines** and an **event loop**. Coroutines use `async def` and yield control back to the event loop using `await`, allowing the single thread to process other tasks while waiting for I/O operations to complete."},
                    {"type": "code", "language": "python", "value": "import asyncio\n\nasync def fetch_data(item_id):\n    print(f'Fetching {item_id}...')\n    await asyncio.sleep(1)  # Simulates network lag, releases control\n    print(f'Done {item_id}!')\n    return {'id': item_id, 'data': 'value'}\n\nasync def main():\n    results = await asyncio.gather(fetch_data(1), fetch_data(2))\n    print(results)\n\n# To run: asyncio.run(main())"},
                    {"type": "callout", "kind": "tip", "title": "Cooperative Principle", "value": "Unlike threads which can be preemptively interrupted at any time, coroutines only yield control when they encounter an explicit `await` statement. If a coroutine contains blocking CPU code (like a long `while` loop), it will block the entire event loop."},
                    {"type": "knowledge_check", "question": "What is if a coroutine contains blocking CPU-bound code like `time.sleep(5)`?", "options": [
                        "It will pause only that specific coroutine while others run.",
                        "It blocks the single thread's event loop, preventing all other coroutines from executing for 5 seconds.",
                        "Python automatically converts it to an asynchronous task."
                    ], "correct_index": 1, "explanation": "asyncio is cooperative and single-threaded. Blocking the thread blocks the event loop. Use `await asyncio.sleep(5)` instead, or run blocking calls in an executor."}
                ]
            }
        ]
    }
]

async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "education_platform"
    db = client[db_name]
    
    # 1. Update/Upsert the Python domain card
    python_domain = {
        "slug": "python",
        "title": "Python Programming",
        "description": "Master Python syntax, functional constructs, control flow, data structures, standard libraries, and concurrent programming."
    }
    await db.domains.update_one({"slug": "python"}, {"$set": python_domain}, upsert=True)
    
    # 2. Clean out duplicate / old python topics to avoid UI mess
    res = await db.topics.delete_many({"domain_slug": "python"})
    print(f"Cleared {res.deleted_count} existing Python topics to prevent duplicates.")
    
    # 3. Seed new rich topics
    inserted_count = 0
    for topic in TOPICS:
        await db.topics.update_one({"slug": topic["slug"]}, {"$set": topic}, upsert=True)
        inserted_count += 1
        print(f"Upserted clean Python topic: {topic['slug']}")
        
    print(f"Successfully seeded {inserted_count} clean Python topics.")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
