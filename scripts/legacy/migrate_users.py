from pymongo import MongoClient

local = MongoClient("mongodb://localhost:27017/education_platform").education_platform
atlas = MongoClient("mongodb://localhost:27017/education_platform").education_platform

collections_to_migrate = ["users", "user_progress", "activity_log", "chat_sessions", "streaks"]

for coll_name in collections_to_migrate:
    local_coll = local[coll_name]
    atlas_coll = atlas[coll_name]
    docs = list(local_coll.find({}))
    print(coll_name, "- local count:", len(docs))
    upserted = 0
    matched = 0
    for doc in docs:
        result = atlas_coll.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        if result.upserted_id:
            upserted += 1
        else:
            matched += 1
    print(coll_name, "- upserted:", upserted, "| already existed/matched:", matched)
