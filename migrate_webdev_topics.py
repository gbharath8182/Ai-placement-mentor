from pymongo import MongoClient

local = MongoClient("mongodb://localhost:27017/education_platform").education_platform
atlas = MongoClient("mongodb://localhost:27017/education_platform").education_platform

docs = list(local.topics.find({"domain_slug": "web-dev"}))
print("local web-dev topics found:", len(docs))

for doc in docs:
    result = atlas.topics.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
    status = "upserted" if result.upserted_id else "matched/updated"
    print(" -", doc.get("slug"), "->", status)

print()
print("Atlas web-dev topics now:", atlas.topics.count_documents({"domain_slug": "web-dev"}))
