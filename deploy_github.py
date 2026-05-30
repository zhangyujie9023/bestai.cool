#!/usr/bin/env python3
"""Deploy: push files to GitHub via API, extracting token from git remote."""
import subprocess, urllib.request, json, sys

# Extract token from existing git remote URL
remote_out = subprocess.run(
    ["git", "remote", "get-url", "origin"],
    capture_output=True, text=True, cwd="/home/zhangyujie9023/bestai-site"
)
remote_url = remote_out.stdout.strip()
token = remote_url.split("://")[1].split("@")[0]

h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
repo = "zhangyujie9023/bestai.cool"
api = "https://api.github.com/repos"

def gh_call(method, path, data=None):
    body = json.dumps(data).encode() if data else None
    url = f"{api}/{repo}/{path}"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    return json.loads(urllib.request.urlopen(req).read())

# Read files
with open("newsletter-draft.md", "rb") as f:
    draft_raw = f.read()
with open("today.html", "rb") as f:
    html_raw = f.read()

# Get latest commit on main
branch = gh_call("GET", "git/refs/heads/main")
latest_sha = branch["object"]["sha"]
print(f"Latest commit on main: {latest_sha}")

# Create blobs
b1 = gh_call("POST", "git/blobs", {"content": draft_raw.decode(), "encoding": "utf-8"})
b2 = gh_call("POST", "git/blobs", {"content": html_raw.decode(), "encoding": "utf-8"})
print(f"Blob 1: {b1['sha']}")
print(f"Blob 2: {b2['sha']}")

# Create tree
tree_data = {
    "base_tree": latest_sha,
    "tree": [
        {"path": "newsletter-draft.md", "mode": "100644", "type": "blob", "sha": b1["sha"]},
        {"path": "today.html", "mode": "100644", "type": "blob", "sha": b2["sha"]},
    ],
}
tree_resp = gh_call("POST", "git/trees", tree_data)
print(f"Tree: {tree_resp['sha']}")

# Create commit
commit_data = {
    "message": "Update newsletter and today.html - May 30, 2026 edition",
    "tree": tree_resp["sha"],
    "parents": [latest_sha],
}
commit_resp = gh_call("POST", "git/commits", commit_data)
print(f"Commit: {commit_resp['sha']}")

# Update reference
ref_data = {"sha": commit_resp["sha"], "force": False}
ref_resp = gh_call("PATCH", "git/refs/heads/main", ref_data)
print(f"Ref updated: {ref_resp['ref']}")

print("\n=== DEPLOYMENT SUCCESSFUL ===")
print("Deployed: newsletter-draft.md, today.html to main branch")
