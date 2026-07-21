import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    card = await db.domains.find_one({"slug": "sde"})
    print("=== domains card ===")
    print(json.dumps({k: v for k, v in card.items() if k != "_id"}, indent=2, ensure_ascii=False))

    details = await db.domain_details.find_one({"domain_slug": "sde"})
    print("\n=== domain_details summary ===")
    print("topics:", [t["name"] for t in details["topics"]])
    print("roadmap tiers:", [r["tier"] for r in details["roadmap"]])
    print("skills:", [s["name"] for s in details["skills"]])
    print("projects:", [p["title"] for p in details["projects"]])
    print("company_prep groups:", [c["group_name"] for c in details["company_prep"]])

asyncio.run(main())