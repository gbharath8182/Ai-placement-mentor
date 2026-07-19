import re

path = "frontend/js/roadmap.js"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

if "openMockInterviewModal" in content:
    print("SKIPPED: already patched")
else:
    pattern = re.compile(
        r"(<p><strong>HR questions:</strong> \$\{chips\(d\.interview_prep \? d\.interview_prep\.hr_questions : \[\]\)\}</p>)(\s*)</section>"
    )
    button_html = (
        r'\1\2<button class="btn-primary mi-start-btn" '
        r"onclick=\"openMockInterviewModal('${d.domain_slug}')\">"
        r'Start Mock Interview</button>\2</section>'
    )
    new_content, count = pattern.subn(button_html, content)
    assert count == 1, f"PATCH FAILED: expected 1 match, found {count} - check roadmap.js content"

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    print("roadmap.js patched successfully")