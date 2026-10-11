from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/education_platform")
db = client.education_platform

def slugify(text):
    return text.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "and").replace(",", "")

def make_content_blocks(topic):
    blocks = []
    if topic.get("description"):
        blocks.append({"type": "heading", "level": 2, "value": "Overview"})
        blocks.append({"type": "text", "value": topic["description"]})
    if topic.get("importance"):
        blocks.append({"type": "heading", "level": 2, "value": "Why It Matters"})
        blocks.append({"type": "text", "value": topic["importance"]})
    if topic.get("practice_questions"):
        blocks.append({"type": "heading", "level": 2, "value": "Practice Questions"})
        for q in topic["practice_questions"]:
            blocks.append({"type": "text", "value": "- " + q})
    if topic.get("interview_questions"):
        blocks.append({"type": "heading", "level": 2, "value": "Interview Questions"})
        for q in topic["interview_questions"]:
            blocks.append({"type": "text", "value": "- " + q})
    return blocks

for domain_slug in ["ml", "python"]:
    doc = db.domain_details.find_one({"domain_slug": domain_slug})
    if not doc or not doc.get("topics"):
        print(domain_slug, "- no topics found in domain_details, skipping")
        continue

    for topic in doc["topics"]:
        name = topic.get("name") or topic.get("title") or "Untitled"
        slug = f"{domain_slug}-{slugify(name)}"

        existing = db.topics.find_one({"slug": slug})
        if existing:
            print("SKIP -- already exists:", slug)
            continue

        new_doc = {
            "slug": slug,
            "title": name,
            "domain_slug": domain_slug,
            "difficulty": topic.get("difficulty", "beginner"),
            "subtopics": [
                {
                    "title": name,
                    "content_blocks": make_content_blocks(topic)
                }
            ]
        }
        result = db.topics.insert_one(new_doc)
        print("Inserted:", slug, "->", result.inserted_id)

print()
print("Final counts:")
print("ml:", db.topics.count_documents({"domain_slug": "ml"}))
print("python:", db.topics.count_documents({"domain_slug": "python"}))
