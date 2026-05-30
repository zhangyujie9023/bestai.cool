#!/usr/bin/env python3
"""
bestai.cool Newsletter Sender
- Reads newsletter-draft.md
- Renders to beautiful card-based HTML email
- Sends via Resend API
"""

import re
import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ── Config ──────────────────────────────────────────────────────────
RESEND_KEY = os.environ.get("RESEND_KEY", "") or "re_Fnhyk1nF_5suGWzCnvLV1jqvsF7zUbZYX"
FROM_EMAIL = "newsletter@bestai.cool"
TO_EMAIL = "251554642@qq.com"
SUBJECT_PREFIX = "bestai.cool AI 资讯速递"

# ── HTML Template ───────────────────────────────────────────────────

CARD_CSS = """
/* Email-safe inline styles for each card */
.card {
    background-color: #ffffff;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border: 1px solid #eef1ff;
}
.card-title {
    font-size: 17px;
    font-weight: 700;
    color: #1e293b;
    line-height: 1.4;
    margin: 0 0 10px 0;
}
.card-title .tag {
    display: inline-block;
    font-size: 12px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    margin-right: 8px;
    vertical-align: middle;
}
.card-body {
    font-size: 14px;
    color: #475569;
    line-height: 1.7;
    margin: 0 0 12px 0;
}
.card-insight {
    background: #f5f7ff;
    border-left: 3px solid #6366f1;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 0 0 12px 0;
    font-size: 13px;
    color: #334155;
    line-height: 1.6;
}
.card-insight strong {
    color: #6366f1;
}
.card-link {
    font-size: 13px;
}
.card-link a {
    color: #6366f1;
    text-decoration: none;
    font-weight: 600;
    border-bottom: 1px dashed #c7d2fe;
}
.card-link a:hover {
    color: #4f46e5;
}
.divider {
    height: 1px;
    background: linear-gradient(90deg, #eef1ff, #6366f1, #eef1ff);
    margin: 32px 0;
}
"""

def build_html_email(items, date_str, email=""):
    """Build full HTML email with cards."""
    cards_html = ""
    for i, item in enumerate(items):
        cards_html += render_card(item, i)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<!--[if mso]>
<style type="text/css">
    .card {{ border-collapse: collapse; }}
</style>
<![endif]-->
<title>bestai.cool 每日 AI 资讯</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f7ff;font-family:'-apple-system','BlinkMacSystemFont','Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei','Helvetica Neue',Arial,sans-serif;">

<!-- Preview text (hidden) -->
<div style="display:none;font-size:1px;color:#f5f7ff;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
  📬 {date_str} — 本期 {len(items)} 条 AI 资讯，涵盖模型发布、开源进展、行业重组、融资动态等热点
</div>

<!-- Main container -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7ff;">
<tr>
<td align="center" style="padding:0;">

<!-- Outer table: max 600px -->
<table role="presentation" width="100%" style="max-width:600px;margin:0 auto;" cellpadding="0" cellspacing="0">

<!-- ── Header ── -->
<tr>
<td style="padding:32px 20px 0 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr>
<td style="text-align:center;padding-bottom:24px;">
<!-- Logo / Brand -->
<div style="font-size:28px;font-weight:800;letter-spacing:-0.5px;">
<span style="color:#6366f1;">bestai</span><span style="color:#94a3b8;">.cool</span>
</div>
<div style="font-size:13px;color:#94a3b8;margin-top:4px;">每日 AI 资讯速递</div>
</td>
</tr>
</table>
</td>
</tr>

<!-- ── Hero Banner ── -->
<tr>
<td style="padding:0 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:16px;">
<tr>
<td style="padding:28px 24px;text-align:center;">
<div style="font-size:22px;font-weight:700;color:#ffffff;line-height:1.3;">AI 资讯速递</div>
<div style="font-size:14px;color:rgba(255,255,255,0.85);margin-top:6px;">{date_str} · {len(items)} 条精选</div>
<div style="font-size:13px;color:rgba(255,255,255,0.7);margin-top:4px;">每天 5 分钟，读懂 AI 圈</div>
</td>
</tr>
</table>
</td>
</tr>

<!-- ── Table of Contents ── -->
<tr>
<td style="padding:20px 20px 0 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;border:1px solid #eef1ff;">
<tr>
<td style="padding:18px 24px;">
<div style="font-size:14px;font-weight:700;color:#1e293b;margin-bottom:10px;">📋 本期导读</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
"""
    # TOC items - 2 per row on desktop
    for idx, item in enumerate(items):
        col = idx % 2
        if col == 0:
            html += '<tr>'
        html += f"""
<td width="50%" style="padding:4px 8px 4px 0;vertical-align:top;font-size:13px;color:#6366f1;line-height:1.4;">
<a href="#item-{idx}" style="color:#6366f1;text-decoration:none;border-bottom:1px solid #e0e7ff;">{item['title_short']}</a>
</td>"""
        if col == 1 or idx == len(items) - 1:
            html += '</tr>'
    
    html += """
</table>
</td>
</tr>
</table>
</td>
</tr>

<!-- ── Newsletter Content ── -->
<tr>
<td style="padding:24px 20px;">
<!-- Section label -->
<div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#94a3b8;margin-bottom:16px;">🔥 今日 AI 头条</div>
"""
    html += cards_html
    
    html += """
</td>
</tr>

<!-- ── Divider ── -->
<tr>
<td style="padding:0 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr>
<td style="height:1px;background:linear-gradient(90deg,#eef1ff,#6366f1,#eef1ff);font-size:1px;line-height:1px;">&nbsp;</td>
</tr>
</table>
</td>
</tr>

<!-- ── Subscription Reminder ── -->
<tr>
<td style="padding:16px 20px 0 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;border:1px solid #eef1ff;">
<tr>
<td style="padding:20px 24px;text-align:center;">
<div style="font-size:14px;color:#475569;line-height:1.6;">
📬 每天早上，AI 资讯直达邮箱<br>
<a href="https://bestai.cool" style="color:#6366f1;font-weight:600;text-decoration:none;">👉 订阅 bestai.cool</a>
</div>
</td>
</tr>
</table>
</td>
</tr>

<!-- ── Footer ── -->
<tr>
<td style="padding:20px 20px 32px 20px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr>
<td style="text-align:center;font-size:12px;color:#94a3b8;line-height:1.8;">
<div style="font-weight:700;font-size:16px;color:#cbd5e1;margin-bottom:4px;">
bestai<span style="color:#64748b;">.cool</span>
</div>
<div>用 ❤ 和 AI 构建 · © 2026 bestai.cool</div>
<div style="margin-top:8px;font-size:13px;color:#64748b;">
📬 推荐给朋友：转发此邮件即可
</div>
<div style="margin-top:8px;">
<a href="https://bestai.cool/unsubscribe?email={email}" style="color:#94a3b8;text-decoration:underline;">退订</a>
</div>
</td>
</tr>
</table>
</td>
</tr>

</table>
</td>
</tr>
</table>
</body>
</html>"""
    return html


def render_card(item, idx):
    """Render a single news item as a card."""
    tag_color = {
        '🔥': 'background:#fee2e2;color:#dc2626;',
        '💡': 'background:#e0e7ff;color:#4f46e5;',
        '📬': 'background:#d1fae5;color:#059669;',
        '👉': 'background:#fef3c7;color:#d97706;',
    }
    tag = item.get('tag', '🔥')
    tag_bg = tag_color.get(tag, 'background:#e0e7ff;color:#4f46e5;')
    
    link_html = ""
    if item.get('link_text') and item.get('link_url'):
        link_html = f"""<div class="card-link" style="font-size:13px;">
🔗 <a href="{item['link_url']}" target="_blank" style="color:#6366f1;text-decoration:none;font-weight:600;border-bottom:1px dashed #c7d2fe;">{item['link_text']}</a>
</div>"""
    
    return f"""
<!-- Card {idx+1} -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" id="item-{idx}" style="background:#ffffff;border-radius:16px;margin-bottom:24px;border:1px solid #eef1ff;">
<tr>
<td style="padding:24px 28px;">

<!-- Title -->
<div style="font-size:17px;font-weight:700;color:#1e293b;line-height:1.4;margin-bottom:10px;">
<span style="display:inline-block;font-size:12px;font-weight:600;padding:2px 10px;border-radius:20px;margin-right:6px;vertical-align:middle;{tag_bg}">{item['tag']}</span>
{item['title']}
</div>

<!-- Body -->
<div style="font-size:14px;color:#475569;line-height:1.7;margin-bottom:12px;">
{item['body']}
</div>

<!-- Insight -->
<div style="background:#f5f7ff;border-left:3px solid #6366f1;border-radius:8px;padding:12px 16px;margin-bottom:12px;font-size:13px;color:#334155;line-height:1.6;">
<strong style="color:#6366f1;">💡 元启划重点：</strong>{item['insight']}
</div>

<!-- Link -->
{link_html}

</td>
</tr>
</table>
"""


def parse_markdown(md_text):
    """Parse newsletter-draft.md into structured items."""
    items = []
    
    # Remove the metadata header before first ---
    parts = md_text.split('---\n')
    # parts[0] is the header, parts[1:] are items separated by ---
    
    for i, part in enumerate(parts):
        if i == 0:
            continue  # skip header
        part = part.strip()
        if not part:
            continue
        
        item = parse_item(part)
        if item:
            items.append(item)
    
    return items

def parse_item(text):
    """Parse a single news item section into dict."""
    item = {}
    
    # Extract title (first line with ## or **)
    title_match = re.search(r'\*\*(.+?)\*\*', text)
    if title_match:
        full_title = title_match.group(1)
        item['title'] = full_title
        # Short version for TOC
        item['title_short'] = full_title[:30] + '…' if len(full_title) > 30 else full_title
    
    # Extract tag (🔥, 💡, etc.)
    tag_match = re.search(r'^(\S)', text.strip())
    if tag_match:
        item['tag'] = tag_match.group(1)
    else:
        item['tag'] = '🔥'
    
    # Extract body (content after 📝, before next section marker)
    # We need to strip the link line from the body
    body_match = re.search(r'📝\s(.+?)(?=\n\n💡|\n\n🔗|\n---|\Z)', text, re.DOTALL)
    if body_match:
        body = body_match.group(1).strip()
        # Remove any markdown bold
        body = re.sub(r'\*\*(.+?)\*\*', r'\1', body)
        # Remove any leftover 🔗 [...] link line from body
        body = re.sub(r'\n🔗\s*\[.*?\]\(.*?\)', '', body).strip()
        item['body'] = body
    else:
        item['body'] = ''
    
    # Extract insight (💡 section)
    insight_match = re.search(r'💡\s\*\*元启划重点：\*\*(.+?)(?=\n\n|\Z)', text, re.DOTALL)
    if insight_match:
        insight = insight_match.group(1).strip()
        insight = re.sub(r'\*\*(.+?)\*\*', r'\1', insight)
        item['insight'] = insight
    else:
        item['insight'] = ''
    
    # Extract link (🔗 section)
    link_match = re.search(r'🔗\s\[(.+?)\]\((.+?)\)', text)
    if link_match:
        item['link_text'] = link_match.group(1)
        item['link_url'] = link_match.group(2)
    
    return item if item.get('title') else None


def get_date_from_md(md_text):
    """Extract date from the markdown header."""
    date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', md_text)
    if date_match:
        return date_match.group(1)
    return "每日速递"


def send_via_resend(to_email, subject, html_content, text_content=""):
    """Send email via Resend API using urllib."""
    url = "https://api.resend.com/emails"
    
    payload = json.dumps({
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
        "text": text_content or "Please view this email in an HTML-compatible client.",
    }).encode()
    
    req = Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {RESEND_KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "bestai.cool/1.0")
    req.add_header("Accept", "application/json")
    
    try:
        resp = urlopen(req, timeout=30)
        result = json.loads(resp.read().decode())
        print(f"✅ Email sent successfully!")
        print(f"   Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return True
    except HTTPError as e:
        body = e.read().decode()
        print(f"❌ HTTP Error {e.code}: {body}")
        return False
    except URLError as e:
        print(f"❌ Network Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    # Read markdown
    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newsletter-draft.md")
    if not os.path.exists(md_path):
        print(f"❌ File not found: {md_path}")
        sys.exit(1)
    
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    # Parse
    date_str = get_date_from_md(md_text)
    items = parse_markdown(md_text)
    print(f"📅 Date: {date_str}")
    print(f"📊 Parsed {len(items)} items:")
    for i, item in enumerate(items):
        print(f"   {i+1}. {item['title_short']}")
        if item.get('link_url'):
            print(f"      🔗 {item['link_text']} → {item['link_url']}")
    
    if not items:
        print("❌ No items parsed. Check markdown format.")
        sys.exit(1)
    
    # Build HTML
    html = build_html_email(items, date_str, TO_EMAIL)
    
    # Save preview
    preview_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newsletter-preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"💾 Preview saved: {preview_path}")
    
    # Send
    subject = f"{SUBJECT_PREFIX} — {date_str}"
    print(f"\n📧 Sending to: {TO_EMAIL}")
    print(f"📧 Subject: {subject}")
    
    success = send_via_resend(TO_EMAIL, subject, html)
    
    if success:
        print(f"\n🎉 Done! Check {TO_EMAIL} inbox.")
    else:
        print(f"\n❌ Failed to send.")
        sys.exit(1)


if __name__ == "__main__":
    main()
