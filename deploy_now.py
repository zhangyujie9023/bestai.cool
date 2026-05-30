#!/usr/bin/env python3
"""Deploy via GitHub API. Reads token from file ~/.github_token"""
import json, os, sys, urllib.request

token_path = os.path.expanduser("~/.github_token")
if not os.path.exists(token_path):
    # Fallback: try env var
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("ERROR: No GitHub token found. Create ~/.github_token or set GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)
else:
    with open(token_path) as f:
        token = f.read().strip()

REPO = "zhangyujie9023/bestai.cool"
HEADERS = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
}

def gh(path, method="GET", data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{path}",
        data=body, headers=HEADERS, method=method,
    )
    return json.loads(urllib.request.urlopen(req).read())

# Read files
with open("newsletter-draft.md", "rb") as f: draft_raw = f.read()
with open("today.html", "rb") as f: html_raw = f.read()

# Get latest commit
branch = gh("git/refs/heads/main")
latest_sha = branch["object"]["sha"]
print(f"Latest commit: {latest_sha}")

# Create blobs
b1 = gh("git/blobs", "POST", {"content": draft_raw.decode(), "encoding": "utf-8"})
b2 = gh("git/blobs", "POST", {"content": html_raw.decode(), "encoding": "utf-8"})
print(f"Blobs: {b1['sha']}, {b2['sha']}")

# Create tree
tree = gh("git/trees", "POST", {
    "base_tree": latest_sha,
    "tree": [
        {"path": "newsletter-draft.md", "mode": "100644", "type": "blob", "sha": b1["sha"]},
        {"path": "today.html", "mode": "100644", "type": "blob", "sha": b2["sha"]},
    ],
})
print(f"Tree: {tree['sha']}")

# Create commit
commit = gh("git/commits", "POST", {
    "message": "Update newsletter and today.html - May 30, 2026 edition",
    "tree": tree["sha"],
    "parents": [latest_sha],
})
print(f"Commit: {commit['sha']}")

# Update reference
ref = gh("git/refs/heads/main", "PATCH", {"sha": commit["sha"], "force": False})
print(f"Ref updated: {ref['ref']}")

print("\n=== DEPLOYMENT SUCCESSFUL ===")
print("  - newsletter-draft.md")
print("  - today.html")
