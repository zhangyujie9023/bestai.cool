#!/usr/bin/env python3
"""生成抖音短视频素材：5张宣传卡片 + TTS配音"""
from PIL import Image, ImageDraw, ImageFont
import textwrap, os, subprocess, json

OUT = os.path.expanduser("~/bestai-site/douyin")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920  # 抖音竖屏

# 配色
C_BG = "#0a0a1a"
C_CARD = "rgba(15,15,40,0.95)"
C_INDIGO = "#6366f1"
C_PURPLE = "#8b5cf6"
C_WHITE = "#f1f5f9"
C_SUB = "#94a3b8"
C_ACCENT = "#818cf8"

def draw_card(text_lines, title=None, subtitle=None, num=None):
    img = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(img)
    
    # 背景光晕
    for i in range(3):
        cx, cy = W//2, H//3 + i*400
        r = 600
        for j in range(100, 0, -2):
            alpha = max(0, 8 - j//20)
            c = (99 + i*20, 102 + i*10, 241, alpha)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c if j == 100 else None,
                         outline=None)
            r -= 2
    
    # 卡片
    card_margin = 60
    card_y = 300
    card_h = H - card_y - 120
    draw.rounded_rectangle([card_margin, card_y, W-card_margin, card_y+card_h],
                          radius=30, fill="#0f0f28")
    
    y = card_y + 60
    # 序号
    if num:
        draw.text((W//2, y), f"0{num}", fill=C_ACCENT, font=None, anchor="mt")
        y += 60
    
    # 标题
    if title:
        for t in title:
            draw.text((W//2, y), t, fill=C_WHITE, font=None, anchor="mt")
            y += 80
    
    # 副标题
    if subtitle:
        y += 20
        for s in subtitle:
            draw.text((W//2, y), s, fill=C_SUB, font=None, anchor="mt")
            y += 50
    
    # 正文
    y = card_y + card_h - 150
    for line in text_lines:
        draw.text((W//2, y), line, fill=C_SUB, font=None, anchor="mt")
        y += 45
    
    path = os.path.join(OUT, f"slide_{num or 0}.png")
    img.save(path)
    print(f"✅ {path}")
    return path

# ====== 生成5张幻灯片 ======
slides = [
    {
        "num": 1,
        "title": ["每天1000条AI新闻", "但你只需要这10条"],
        "subtitle": ["bestai.cool · 你的AI资讯助手"],
        "lines": ["多Agent自动监控1000+信息源", "每天精选10条最重要的给你"]
    },
    {
        "num": 2,
        "title": ["每条都有毒舌点评"],
        "subtitle": ["不再看温吞水废话"],
        "lines": ["💡元启划重点", "有态度、说人话、不堆术语"]
    },
    {
        "num": 3,
        "title": ["1000+信息源", "10条精选"],
        "subtitle": ["每天中午，准时推送"],
        "lines": ["永久免费 · 不卖邮箱 · 可随时退订"]
    },
    {
        "num": 4,
        "title": ["不用翻墙", "不用注册App"],
        "subtitle": ["只需一个邮箱"],
        "lines": ["每天中午12:30，资讯直达你的收件箱"]
    },
    {
        "num": 5,
        "title": ["免费订阅 →"],
        "subtitle": ["bestai.cool"],
        "lines": ["用 ❤️ 和 AI 构建"]
    }
]

paths = []
for s in slides:
    p = draw_card(s["lines"], s["title"], s.get("subtitle"), s["num"])
    paths.append(p)

print(f"\n✅ 共生成 {len(paths)} 张幻灯片到 {OUT}")
