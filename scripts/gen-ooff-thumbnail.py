#!/usr/bin/env python3
"""
OOFF TABLE 소셜링 포스트 이미지 생성 스크립트 (3장)
실행: python3 scripts/gen-ooff-thumbnail.py

생성되는 이미지:
  1. ooff-table-book-social-2026-0510.webp  — 썸네일 (hero)
  2. ooff-book-cover-0510.webp              — 본문 1번 (책 클로즈업)
  3. ooff-rolling-paper-0510.webp           — 본문 2번 (롤링페이퍼)
"""

import os, sys, subprocess, urllib.request, json, io
from PIL import Image

# iCloud 시크릿에서 API 키 읽기
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
        "filename": "ooff-table-book-social-2026-0510.webp",
        "size": "1792x1024",
        "prompt": (
            "A moody underground bar in Gangnam Seoul at night, neon colored lights in vivid purple, "
            "blue, and pink illuminate an intimate reading club gathering. Young Korean adults sit around "
            "a low table with books scattered between cocktail glasses. The atmosphere is club-like but "
            "intellectual — UV black lights, glowing book spines, dim dramatic lighting. Cinematic, photorealistic style."
        ),
    },
    {
        "filename": "ooff-book-cover-0510.webp",
        "size": "1024x1024",
        "prompt": (
            "A Korean literary essay book lying open on a dark wooden table, soft warm lamp light from the side. "
            "The book pages glow softly. A cup of tea nearby. Moody, intimate, contemplative atmosphere. "
            "Shot from slightly above. Cinematic still life, photorealistic."
        ),
    },
    {
        "filename": "ooff-rolling-paper-0510.webp",
        "size": "1792x1024",
        "prompt": (
            "A dimly lit bar table at night in Seoul. Several small handwritten notes and a folded paper "
            "are arranged on the dark table among books and glasses. Soft candlelight and neon glow. "
            "Intimate gathering atmosphere, cinematic, photorealistic style."
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
        "model": "dall-e-3",
        "prompt": item["prompt"],
        "n": 1,
        "size": item["size"],
        "quality": "standard",
        "response_format": "url",
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    image_url = data["data"][0]["url"]
    print(f"   URL: {image_url[:70]}...")

    with urllib.request.urlopen(image_url) as resp:
        img = Image.open(io.BytesIO(resp.read())).convert("RGB")

    img.save(out_path, "WEBP", quality=90)
    print(f"✅ 저장: {out_path}")


for item in IMAGES:
    generate_and_save(item)

print("\n🎉 완료! 아래 명령어로 push해주세요:")
print("   git add images/blog/ooff-*.webp")
print("   git commit -m 'asset: OOFF TABLE 소셜링 이미지 3장 추가'")
print("   git push origin main")
