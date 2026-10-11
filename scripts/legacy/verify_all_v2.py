import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform
    domain_slugs = await db.topics.distinct("domain_slug")
    print("Domain slugs found in DB:", domain_slugs)
    for slug in sorted(domain_slugs):
        topics = await db.topics.find({"domain_slug": slug}).to_list(length=None)
        print(f"\n=== DOMAIN: {slug} -- {len(topics)} topics ===")
        for t in topics:
            subtopics = t.get("subtopics", [])
            total_blocks = sum(len(s.get("content_blocks", [])) for s in subtopics)
            diffs = [s.get("difficulty", "none") for s in subtopics]
            problems_count = await db.practice_problems.count_documents({"topic_slug": t.get("slug")})
            print(f"  - {t.get('title', t.get('slug'))} [{t.get('slug')}]: {len(subtopics)} subtopics {diffs}, {total_blocks} content_blocks, {problems_count} practice_problems")

asyncio.run(main())
