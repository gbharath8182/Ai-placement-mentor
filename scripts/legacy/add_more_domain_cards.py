from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/education_platform")
db = client.education_platform

cards = [
    {"slug": "system-design", "title": "System Design", "description": "Core system design concepts -- CDNs, database sharding, load balancing, and scalability -- for architecture interviews."},
    {"slug": "web-dev", "title": "Web Development", "description": "Web fundamentals and browser APIs -- storage, client-server communication, and core web development patterns."},
]

for card in cards:
    r = db.domains.update_one({"slug": card["slug"]}, {"$set": card}, upsert=True)
    print(card["slug"], "-> matched:", r.matched_count, "modified:", r.modified_count, "upserted:", r.upserted_id)
