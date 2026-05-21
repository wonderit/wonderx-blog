#!/usr/bin/env python3
"""
Karpathy Sequoia talk review — 블로그 이미지 생성 스크립트 (4장)
실행: python3 scripts/gen-karpathy-sequoia.py

모델: gpt-image-1 (b64_json 반환)
크기: 1024x1024 또는 1536x1024 (landscape) / 1024x1536 (portrait)
"""

import os, sys, subprocess, urllib.request, json, io, base64
from PIL import Image

SECRET_FILE = os.path.expanduser(
    "~/Library/Mobile Documents/com~apple~CloudDocs/00_wonderx/secrets/api-keys.sh"
)
result = subprocess.run(
    f'source "{SECRET_FILE}" && echo $OPENAI_API_KEY',
    shell=True, executable="/bin/bash", capture_output=True, text=True
)
api_key = result.stdout.strip()
if not api_key:
    sys.exit("❌ OPENAI_API_KEY를 찾지 못했어요. iCloud 시크릿 파일 확인해주세요.")
print("✅ API 키 로드 완료")

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "images", "blog")
os.makedirs(OUT_DIR, exist_ok=True)

IMAGES = [
    {
        "filename": "karpathy-sequoia-hero.webp",
        "size": "1536x1024",
        "prompt": (
            "Editorial illustration in muted earthy tones — beige, deep navy, rust. "
            "A lone thinker sits in front of a giant glowing chalkboard scribbled with handwritten equations. "
            "Soft warm spotlight from above. Half the chalkboard fades into a faint stream of code. "
            "Cinematic, contemplative, magazine-cover composition. Photorealistic with a painterly finish, no rendered text."
        ),
    },
    {
        "filename": "karpathy-sequoia-agents-meeting.webp",
        "size": "1536x1024",
        "prompt": (
            "Two minimalist glowing orbs of soft light face each other across a long wooden conference table, "
            "exchanging glowing thread-like data lines between them. Two humans stand at the far ends of the room, "
            "casually waving to each other, hands in pockets. Warm beige walls, large windows with city skyline, "
            "evening light. Editorial illustration, muted palette, photorealistic mood. No visible text or logos."
        ),
    },
    {
        "filename": "karpathy-sequoia-llms-txt.webp",
        "size": "1024x1024",
        "prompt": (
            "A clean overhead shot of two stacked documents on a dark walnut desk. "
            "The top document is densely typeset with neat structured plain-text markup, glowing faintly. "
            "The bottom document is a colorful glossy designed brochure with photos. "
            "A subtle robot hand reaches for the top one, a human hand for the bottom one. "
            "Minimalist editorial photography, warm soft lighting, no readable text. Cinematic still life."
        ),
    },
    {
        "filename": "karpathy-sequoia-token-economy.webp",
        "size": "1536x1024",
        "prompt": (
            "Editorial illustration — a dashboard view in a modern office. "
            "Soft beige and deep navy palette. A monitor shows abstract bar-chart bars rising, "
            "with floating glowing pill-shaped icons drifting upward like coins. "
            "A blurred human silhouette sits typing in front of it. "
            "Mood: quiet, contemplative, slightly futuristic. Photorealistic, magazine spread style. "
            "No readable text or specific numbers."
        ),
    },
]

def generate_and_save(item):
    filename = item["filename"]
    out_path = os.path.join(OUT_DIR, filename)

    if os.path.exists(out_path):
        print(f"⏭️  이미 존재함, 건너뜀: {filename}")
        return

    print(f"\n🎨 생성 중: {filename}")
    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": item["prompt"],
        "n": 1,
        "size": item["size"],
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {e.code}: {err_body[:400]}")
        raise

    b64 = data["data"][0]["b64_json"]
    img_bytes = base64.b64decode(b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img.save(out_path, "WEBP", quality=88)
    print(f"✅ 저장: {out_path} ({img.size[0]}x{img.size[1]})")


for item in IMAGES:
    generate_and_save(item)

print("\n🎉 완료!")
