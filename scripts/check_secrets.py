import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    re.compile(r"xkeysib-[a-f0-9]{32,}"),
    re.compile(r"mongodb(?:\+srv)?://[^<>\s/@]+:[^<>\s/@]+@"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def scan(staged=False):
    command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"] if staged else ["git", "ls-files", "-z"]
    paths = subprocess.check_output(command, cwd=ROOT).decode().split("\0")
    findings = []
    for path in filter(None, paths):
        if path.startswith(".env") and path != ".env.example":
            findings.append((path, "environment file must not be committed"))
            continue
        if path.startswith(("backups/", "artifacts/", ".venv/")):
            findings.append((path, "local generated data must not be committed"))
            continue
        file = ROOT / path
        if not file.is_file():
            continue
        if staged:
            raw = subprocess.check_output(["git", "show", ":" + path], cwd=ROOT)
        else:
            raw = file.read_bytes()
        if b"\0" in raw:
            continue
        content = raw.decode("utf-8", errors="replace")
        if any(pattern.search(content) for pattern in PATTERNS):
            findings.append((path, "possible credential material detected"))
    for path, description in findings:
        print(f"{path}: {description}")
    print(f"Secret scan: {len(findings)} findings in {sum(bool(path) for path in paths)} files; no secret values printed.")
    return 1 if findings else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Basic secret-pattern and sensitive-file checks; does not replace provider key rotation or a dedicated scanner.")
    parser.add_argument("--staged", action="store_true")
    sys.exit(scan(parser.parse_args().staged))
