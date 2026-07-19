import json
with open("dsa_template_dump.json", "r", encoding="utf-8") as f:
    doc = json.load(f)

print("=== ROADMAP (first tier) ===")
print(json.dumps(doc["roadmap"][0], indent=2, ensure_ascii=False))

print("\n=== SKILLS (first entry) ===")
print(json.dumps(doc["skills"][0], indent=2, ensure_ascii=False))

print("\n=== PROJECTS (first entry) ===")
print(json.dumps(doc["projects"][0], indent=2, ensure_ascii=False))

print("\n=== INTERVIEW_PREP (full) ===")
print(json.dumps(doc["interview_prep"], indent=2, ensure_ascii=False))

print("\n=== COMPANY_PREP (first entry) ===")
print(json.dumps(doc["company_prep"][0], indent=2, ensure_ascii=False))