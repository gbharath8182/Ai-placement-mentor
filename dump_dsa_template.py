import asyncio, json
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    doc = await client.education_platform.domain_details.find_one({"domain_slug": "dsa"})
    with open("dsa_template_dump.json", "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, default=str, ensure_ascii=False)
    print("Dumped. Top-level keys:", list(doc.keys()) if doc else "NOT FOUND")

asyncio.run(main())