import json
with open("dsa_template_dump.json", "r", encoding="utf-8") as f:
    doc = json.load(f)
print(json.dumps(doc["topics"][0], indent=2, ensure_ascii=False))