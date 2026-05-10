#!/usr/bin/env python3
"""
OOFF TABLE 소셜링 포스트 썸네일 생성 스크립트
실행: python3 scripts/gen-ooff-thumbnail.py
"""

import os, sys, subprocess, urllib.request, json

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

# DALL-E 요청
prompt = (
    "A moody underground bar in Gangnam Seoul at night, neon colored lights in vivid purple, "
    "blue, and pink illuminate an intimate reading club gathering. Young Korean adults sit around "
    "a low table with books scattered between cocktail glasses. The atmosphere is club-like but "
    "intellectual — UV black lights, glowing book spines, dim dramatic lighting. Cinematic, photorealistic style."
)

payload = json.dumps({
    "model": "dall-e-3",
    "prompt": prompt,
    "n": 1,
    "size": "1792x1024",
    "quality": "standard",
    "response_format": "url"
}).encode()

req = urllib.request.Request(
    "https://api.openai.com/v1/images/generations",
    data=payload,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
)

print("🎨 DALL-E 이미지 생성 중...")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

image_url = data["data"][0]["url"]
print(f"✅ 이미지 URL: {image_url[:80]}...")

# 이미지 다운로드 → webp 변환 후 저장
out_dir = os.path.join(os.path.dirname(__file__), "..", "images", "blog")
os.makedirs(out_dir, exist_ok=True)
png_path = os.path.join(out_dir, "ooff-table-book-social-2026-0510.png")
webp_path = os.path.join(out_dir, "ooff-table-book-social-2026-0510.webp")

urllib.request.urlretrieve(image_url, png_path)
print(f"✅ PNG 저장: {png_path}")

# PNG → WebP 변환 (sips 사용, macOS 기본 툴)
subprocess.run(["sips", "-s", "format", "webp", png_path, "--out", webp_path], check=True)
os.remove(png_path)
print(f"✅ WebP 저장: {webp_path}")
print("\n🎉 완료! 이제 git add + commit + push 해주세요:")
print(f"   git add images/blog/ooff-table-book-social-2026-0510.webp")
print(f"   git commit -m 'asset: OOFF TABLE 소셜링 썸네일 추가'")
print(f"   git push origin main")
