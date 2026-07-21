from pymongo import MongoClient

local = MongoClient("mongodb://localhost:27017/education_platform").education_platform
atlas = MongoClient("mongodb://localhost:27017/education_platform").education_platform

# Migrate missing topics (by slug)
atlas_slugs = set(t["slug"] for t in atlas.topics.find({}, {"slug": 1}))
missing_topics = list(local.topics.find({"slug": {"$nin": list(atlas_slugs)}}))
print("Migrating", len(missing_topics), "missing topics...")
for doc in missing_topics:
    atlas.topics.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
    print(" -", doc.get("slug"))

# Migrate ALL practice_problems by _id (safe upsert, no duplicates)
local_pp = list(local.practice_problems.find({}))
print()
print("Reconciling", len(local_pp), "practice_problems...")
upserted = 0
for doc in local_pp:
    result = atlas.practice_problems.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
    if result.upserted_id:
        upserted += 1
print("Newly upserted:", upserted)

print()
print("Final counts:")
print("topics:", atlas.topics.count_documents({}))
print("practice_problems:", atlas.practice_problems.count_documents({}))
