import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.education_platform

    # ---------- Expand html-css (fetch existing, append new subtopics) ----------
    html_css = await db.topics.find_one({"slug": "html-css"})
    existing_subtopics = html_css.get("subtopics", [])

    new_html_css_subtopics = [
        {
            "title": "Responsive Design: Media Queries & the Mobile-First Mindset",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Designing for Every Screen Size"},
                {"type": "text", "value": "Responsive design means a page adapts its layout to the screen it's viewed on, rather than forcing a fixed desktop layout onto a phone. Media queries are CSS rules that only apply when the viewport matches certain conditions, most commonly a minimum or maximum width."},
                {"type": "list", "ordered": False, "items": [
                    "`@media (max-width: 768px) { ... }` -- apply styles only below 768px wide (typical tablet/phone breakpoint)",
                    "Mobile-first: write base styles for small screens first, then use `min-width` media queries to add complexity for larger screens",
                    "`<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">` -- required in the HTML head or mobile browsers render at a zoomed-out desktop width by default",
                    "Relative units (`%`, `rem`, `vw`/`vh`) adapt better across screen sizes than fixed `px` values"
                ]},
                {"type": "callout", "kind": "tip", "title": "Mobile-First Is Usually Less CSS Overall", "value": "Starting with the simplest (mobile) layout and adding complexity for larger screens tends to produce less, more maintainable CSS than starting desktop-first and trying to cram a complex layout into a small screen with overrides."},
                {"type": "code", "language": "css", "value": "/* Mobile-first base styles */\n.card {\n  display: block;\n  width: 100%;\n  padding: 1rem;\n}\n\n/* Add a two-column layout once there's room for it */\n@media (min-width: 768px) {\n  .card {\n    display: inline-block;\n    width: 48%;\n  }\n}"},
                {"type": "resource_link", "label": "\U0001F4C4 MDN -- Responsive Design", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design"}
            ]
        },
        {
            "title": "The CSS Box Model & Specificity",
            "difficulty": "beginner",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Every Element Is a Box"},
                {"type": "text", "value": "Every HTML element is rendered as a rectangular box made of four layers, from the inside out: content, padding, border, and margin. Understanding this layout model explains why an element's actual rendered size is often larger than the width you set -- padding and border are added on top by default."},
                {"type": "list", "ordered": False, "items": [
                    "`box-sizing: border-box` -- makes `width`/`height` include padding and border (almost always what you actually want)",
                    "`margin` -- transparent space outside the border, between this element and its neighbors",
                    "`padding` -- space between the content and the border, inside the element's own background",
                    "CSS specificity, roughly low to high: element selector < class selector < id selector < inline `style=\"\"` < `!important`"
                ]},
                {"type": "callout", "kind": "warning", "title": "!important Is a Last Resort, Not a Habit", "value": "Reaching for `!important` to win a specificity fight usually just moves the problem -- the next override needs its own `!important`, and debugging which rule actually applies becomes much harder. Fixing the underlying selector specificity is almost always the better long-term move."},
                {"type": "code", "language": "css", "value": "/* Without border-box, width:200px + padding:20px = 240px actual width */\n* {\n  box-sizing: border-box;\n}\n\n.button {\n  width: 200px;\n  padding: 20px;\n  border: 2px solid black;\n  /* actual rendered width stays 200px with border-box */\n}"},
                {"type": "resource_link", "label": "\U0001F4C4 MDN -- The Box Model", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/The_box_model"}
            ]
        }
    ]

    await db.topics.update_one(
        {"slug": "html-css"},
        {"$set": {"subtopics": existing_subtopics + new_html_css_subtopics}}
    )
    print(f"html-css: {len(existing_subtopics)} existing subtopics -> {len(existing_subtopics) + len(new_html_css_subtopics)} total")

    # ---------- Expand js-essentials (fetch existing, append new subtopics) ----------
    js_essentials = await db.topics.find_one({"slug": "js-essentials"})
    existing_js_subtopics = js_essentials.get("subtopics", [])

    new_js_subtopics = [
        {
            "title": "DOM Manipulation & Event Handling",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "Making Pages Interactive"},
                {"type": "text", "value": "The DOM (Document Object Model) is the browser's live, in-memory representation of the page as a tree of objects. JavaScript reads and modifies this tree directly -- select an element, change its content or style, and the browser re-renders it immediately."},
                {"type": "list", "ordered": False, "items": [
                    "`document.querySelector(\"#id\")` / `document.querySelectorAll(\".class\")` -- select one or many elements using any CSS selector",
                    "`element.addEventListener(\"click\", handler)` -- attach a handler function without overwriting any existing handlers on the same event",
                    "`element.textContent` -- get/set the plain text inside an element; `element.classList.add/remove/toggle(...)` -- manage CSS classes",
                    "`document.createElement(\"div\")` + `parent.appendChild(newEl)` -- build and insert new elements programmatically"
                ]},
                {"type": "callout", "kind": "tip", "title": "addEventListener Over the onclick Attribute", "value": "Setting `element.onclick = fn` can only ever hold one handler at a time -- assigning a second one silently overwrites the first. `addEventListener` allows multiple independent handlers on the same element and event, and is the standard modern approach."},
                {"type": "code", "language": "javascript", "value": "const button = document.querySelector(\"#submit-btn\");\n\nbutton.addEventListener(\"click\", function (event) {\n  event.preventDefault();\n  const input = document.getElementById(\"username\");\n  console.log(`Submitted: ${input.value}`);\n});\n\n// Build and insert a new element dynamically\nconst newDiv = document.createElement(\"div\");\nnewDiv.classList.add(\"card\");\nnewDiv.textContent = \"Dynamically created\";\ndocument.body.appendChild(newDiv);"},
                {"type": "resource_link", "label": "\U0001F4C4 MDN -- Introduction to Events", "url": "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Building_blocks/Events"}
            ]
        },
        {
            "title": "Modern JavaScript: Destructuring, Spread & Classes",
            "difficulty": "intermediate",
            "content_blocks": [
                {"type": "heading", "level": 2, "value": "ES6+ Syntax You'll See in Every Modern Codebase"},
                {"type": "text", "value": "Since ES6 (2015), JavaScript added several syntax features that dramatically shorten common patterns: destructuring pulls values out of objects/arrays directly into named variables, the spread operator `...` expands an iterable in place, and `class` syntax provides a cleaner way to write constructor-function-based inheritance that already existed under the hood."},
                {"type": "list", "ordered": False, "items": [
                    "`const { name, age = 18 } = obj;` -- destructure with a default value if the key is missing",
                    "`const { name, ...rest } = obj;` -- pull out `name`, collect everything else into `rest`",
                    "`const combined = [...arr1, ...arr2];` -- spread arrays together without mutating either original",
                    "`class Dog extends Animal { ... }` with `super(...)` -- classical-looking inheritance syntax over JS's prototype chain"
                ]},
                {"type": "callout", "kind": "info", "title": "Arrow Functions Don't Rebind this", "value": "A regular `function` gets its own `this` depending on how it's called, which is a classic source of bugs inside callbacks and class methods. Arrow functions (`x => x * x`) instead inherit `this` from their surrounding scope at the point they're defined -- this is often why they're preferred for callbacks inside class methods or event handlers."},
                {"type": "code", "language": "javascript", "value": "const { name, age = 18, ...rest } = { name: \"Alex\", city: \"Delhi\" };\nconsole.log(name, age, rest);   // Alex 18 { city: 'Delhi' }\n\nconst arr1 = [1, 2, 3];\nconst arr2 = [...arr1, 4, 5];\nconsole.log(arr2);              // [1, 2, 3, 4, 5]\n\nclass Animal {\n  constructor(name) { this.name = name; }\n  speak() { return `${this.name} makes a sound.`; }\n}\nclass Dog extends Animal {\n  speak() { return `${this.name} barks.`; }\n}\nconsole.log(new Dog(\"Rex\").speak());   // Rex barks."},
                {"type": "resource_link", "label": "\U0001F4C4 Free Textbook: Eloquent JavaScript -- Chapter 4 (Data Structures)", "url": "https://eloquentjavascript.net/04_data.html"}
            ]
        }
    ]

    await db.topics.update_one(
        {"slug": "js-essentials"},
        {"$set": {"subtopics": existing_js_subtopics + new_js_subtopics}}
    )
    print(f"js-essentials: {len(existing_js_subtopics)} existing subtopics -> {len(existing_js_subtopics) + len(new_js_subtopics)} total")

    # ---------- New practice problems ----------
    problems = [
        {
            "topic_slug": "js-essentials",
            "title": "Find the Longest Word",
            "difficulty": "easy",
            "description": "Read a line of space-separated words using prompt(). Print the longest word. If there's a tie, print whichever one appears first.\n\nExample:\nInput: the quick brown fox jumps\nOutput: quick",
            "starter_code": "const str = prompt();\nconst words = str.split(/\\s+/).filter(Boolean);\nconst longest = words.reduce((a, b) => b.length > a.length ? b : a, \"\");\nconsole.log(longest);\n",
            "test_cases": [
                {"input": "the quick brown fox jumps", "expected_output": "quick"},
                {"input": "a bb ccc", "expected_output": "ccc"},
                {"input": "cat dog fox", "expected_output": "cat"}
            ]
        },
        {
            "topic_slug": "js-essentials",
            "title": "Average of an Array",
            "difficulty": "easy",
            "description": "Read a line of space-separated numbers using prompt(). Print their average, formatted to 2 decimal places.\n\nExample:\nInput: 1 2 3 4 5\nOutput: 3.00",
            "starter_code": "const arr = prompt().trim().split(/\\s+/).map(Number);\nconst total = arr.reduce((sum, n) => sum + n, 0);\nconst avg = total / arr.length;\nconsole.log(avg.toFixed(2));\n",
            "test_cases": [
                {"input": "1 2 3 4 5", "expected_output": "3.00"},
                {"input": "10 20 30", "expected_output": "20.00"},
                {"input": "7", "expected_output": "7.00"}
            ]
        }
    ]
    result = await db.practice_problems.insert_many(problems)
    print(f"Inserted {len(result.inserted_ids)} new js-essentials practice problems")

asyncio.run(main())
