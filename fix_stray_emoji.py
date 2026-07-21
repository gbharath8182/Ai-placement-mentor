import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

BAD_CHARS = ["\U0001F5C2", "\U0001F4DD"]  # stray emoji mistakenly used in place of "&"

def clean(value):
    if isinstance(value, str):
        for ch in BAD_CHARS:
            value = value.replace(ch, "&")
        return value
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017/education_platform")
    db = client.education_platform

    topic = await db.topics.find_one({"slug": "python-strings-regex"})
    if not topic:
        print("Topic not found")
        return

    fixed = clean(topic)
    await db.topics.replace_one({"_id": topic["_id"]}, fixed)
    print("Fixed topic title:", fixed["title"])
    for st in fixed["subtopics"]:
        print("  -", st["title"])
        for block in st["content_blocks"]:
            if block.get("type") == "resource_link":
                print("      link:", block["label"])

asyncio.run(main())
