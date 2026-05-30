import json, base64, os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")
RESEND_KEY = os.environ.get("RESEND_KEY", "")
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

            # 发送欢迎邮件（通过 Resend）
            if RESEND_KEY:
                try:
                    welcome_html = f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;padding:30px;max-width:600px;margin:auto">
<h2 style="color:#2563eb">🎉 欢迎加入 bestai.cool！</h2>
<p>你好，<strong>{email}</strong>！</p>
<p>感谢你订阅 bestai.cool AI 资讯助手。从明天开始，每天 <strong>中午 12:30</strong> 你将准时收到我们精心整理的 AI 资讯精选，涵盖最新技术动态、实用工具和深度解读。</p>
<p style="color:#6b7280;font-size:14px">如果你不希望再收到邮件，可以随时回复此邮件退订。</p>
<hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0">
<p style="color:#9ca3af;font-size:12px">bestai.cool · 让你的 AI 视野领先一步</p>
</body></html>"""
                    email_payload = json.dumps({
                        "from": "bestai.cool <subscribe@bestai.cool>",
                        "to": email,
                        "subject": "🎉 欢迎订阅 bestai.cool AI 资讯助手",
                        "html": welcome_html
                    }).encode()
                    req = Request("https://api.resend.com/emails",
                                  data=email_payload,
                                  method="POST")
                    req.add_header("Authorization", f"Bearer {RESEND_KEY}")
                    req.add_header("Content-Type", "application/json")
                    urlopen(req, timeout=10)
                except Exception:
                    # 邮件发送失败不影响订阅流程
                    pass

            return self._json(200, {"success": True, "email": email, "total": len(subs)})
        except Exception as e:
            return self._json(500, {"error": "failed to save", "detail": str(e)})
    
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
