#!/usr/bin/env python3
"""Compare reviewed pstack files with Lauren's upstream; never install or execute fetched content."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/cursor/plugins.git"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Only verify the retained source hashes")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "upstream/pstack/manifest.json").read_text())
    if manifest["repository"] != REPO or not re.fullmatch(r"[0-9a-f]{40}", manifest["revision"]):
        raise ValueError("Expected Lauren's cursor/plugins upstream and a full pinned SHA")
    ref = manifest["revision"]
    if not args.offline:
        result = subprocess.run(["git", "ls-remote", REPO, "refs/heads/main"], text=True, capture_output=True, check=True, timeout=30)
        ref = result.stdout.split()[0]
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError("Upstream did not return a full SHA")
    rows = []
    for item in manifest["files"]:
        path = item["path"]
        if not path.startswith("pstack/") or ".." in Path(path).parts:
            raise ValueError("Invalid upstream path")
        local = ROOT / "upstream/pstack/source" / path.removeprefix("pstack/")
        if hashlib.sha256(local.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Retained source changed: {path}")
        digest = item["sha256"]
        if not args.offline:
            url = f"https://raw.githubusercontent.com/cursor/plugins/{ref}/{path}"
            with urlopen(Request(url, headers={"User-Agent": "my-ai-config-upstream-check"}), timeout=30) as response:
                digest = hashlib.sha256(response.read()).hexdigest()
        rows.append({"path": path, "changed": digest != item["sha256"], "url": f"https://github.com/cursor/plugins/blob/{ref}/{path}"})
    changed = any(row["changed"] for row in rows)
    print(json.dumps({"status": "review-needed" if changed else "unchanged", "pinned": manifest["revision"], "checked": ref, "offline": args.offline, "files": rows}, indent=2))
    return int(changed)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(2)
