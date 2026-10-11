from pymongo import MongoClient

local = MongoClient("mongodb://localhost:27017/education_platform").education_platform
atlas = MongoClient("mongodb://localhost:27017/education_platform").education_platform

collections = set(local.list_collection_names()) | set(atlas.list_collection_names())

print("=" * 70)
for coll_name in sorted(collections):
    local_count = local[coll_name].count_documents({})
    atlas_count = atlas[coll_name].count_documents({})
    flag = "  <-- MISMATCH" if local_count != atlas_count else ""
    print(f"{coll_name:25s} local={local_count:5d}  atlas={atlas_count:5d}{flag}")
print("=" * 70)

print()
print("--- Detailed diff for 'topics' collection ---")
local_slugs = set(t["slug"] for t in local.topics.find({}, {"slug": 1}))
atlas_slugs = set(t["slug"] for t in atlas.topics.find({}, {"slug": 1}))
missing_in_atlas = local_slugs - atlas_slugs
print("Topics in local but MISSING from Atlas:", len(missing_in_atlas))
for slug in sorted(missing_in_atlas):
    print(" -", slug)

print()
print("--- Detailed diff for 'domain_details' collection ---")
local_dd = set(d["domain_slug"] for d in local.domain_details.find({}, {"domain_slug": 1}))
atlas_dd = set(d["domain_slug"] for d in atlas.domain_details.find({}, {"domain_slug": 1}))
print("domain_details in local but MISSING from Atlas:", local_dd - atlas_dd)

print()
print("--- Detailed diff for 'domains' collection ---")
local_d = set(d["slug"] for d in local.domains.find({}, {"slug": 1}))
atlas_d = set(d["slug"] for d in atlas.domains.find({}, {"slug": 1}))
print("domains in local but MISSING from Atlas:", local_d - atlas_d)

print()
print("--- Detailed diff for 'practice_problems' collection ---")
local_pp = local.practice_problems.count_documents({})
atlas_pp = atlas.practice_problems.count_documents({})
print(f"local: {local_pp}, atlas: {atlas_pp}")
