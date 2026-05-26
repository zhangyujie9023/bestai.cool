import json, base64, os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")
GH_REPO = "zhangyujie9023/bestai.cool"
GH_API = f"https://api.github.com/repos/{GH_REPO}"
SUB_PATH = "subscribers.json"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)
        email = (params.get('email') or [''])[0].strip().lower()
        
        if not email or '@' not in email:
            return self._json(400, {"error": "invalid email"})
        
        try:
            # 获取现有 subscribers.json
            req = Request(f"{GH_API}/contents/{SUB_PATH}")
            req.add_header("Authorization", f"Bearer {GH_TOKEN}")
            req.add_header("Accept", "application/vnd.github+json")
            
            try:
                resp = urlopen(req, timeout=10)
                data = json.loads(resp.read())
                sha = data.get("sha")
                content = base64.b64decode(data["content"]).decode()
                subs = json.loads(content) if content.strip() else []
            except Exception:
                sha = None
                subs = []
            
            # 添加新订阅者
            if email not in subs:
                subs.append(email)
            
            # 写回 GitHub
            new_content = json.dumps(subs, ensure_ascii=False, indent=2)
            payload = {
                "message": f"📬 新订阅: {email}",
                "content": base64.b64encode(new_content.encode()).decode(),
                "sha": sha
            }
            req = Request(f"{GH_API}/contents/{SUB_PATH}",
                data=json.dumps(payload).encode(),
                method="PUT")
            req.add_header("Authorization", f"Bearer {GH_TOKEN}")
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/vnd.github+json")
            urlopen(req, timeout=10)
            
            return self._json(200, {"success": True, "email": email, "total": len(subs)})
        except Exception as e:
            return self._json(200, {"success": True, "email": email, "note": str(e)})
    
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
