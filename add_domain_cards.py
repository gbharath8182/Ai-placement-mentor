from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/education_platform")
db = client.education_platform

cards = [
    {"slug": "ml", "title": "Machine Learning", "description": "Building systems that learn patterns from data -- classical statistical learning through modern deep learning and Transformer architectures."},
    {"slug": "python", "title": "Python Programming", "description": "Core Python skills for interviews and real-world engineering -- functions, files, strings/regex, web scraping, and data handling."},
    {"slug": "dsa", "title": "Data Structures & Algorithms", "description": "Foundational DSA topics -- backtracking, DP, graphs, greedy, heaps, stacks/queues -- for coding interviews."},
]

for card in cards:
    r = db.domains.update_one({"slug": card["slug"]}, {"$set": card}, upsert=True)
    print(card["slug"], "-> matched:", r.matched_count, "modified:", r.modified_count, "upserted:", r.upserted_id)
