path = r"C:\Users\navaneeth\Ai-placement-mentor\backend\models.py"
with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

if "difficulty: Optional[str] = None" in content:
    print("ALREADY PATCHED - no change needed")
else:
    marker_lf = "class SubTopic(BaseModel):\n    title: str\n    content_blocks: List[Dict[str, Any]]"
    marker_crlf = marker_lf.replace("\n", "\r\n")

    if marker_lf in content:
        content = content.replace(marker_lf, marker_lf + "\n    difficulty: Optional[str] = None", 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("PATCHED (LF): difficulty field added to SubTopic model")
    elif marker_crlf in content:
        content = content.replace(marker_crlf, marker_crlf + "\r\n    difficulty: Optional[str] = None", 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("PATCHED (CRLF): difficulty field added to SubTopic model")
    else:
        idx = content.find("class SubTopic")
        print("MARKER NOT FOUND - paste this back to me:")
        print(repr(content[idx:idx+250]))
