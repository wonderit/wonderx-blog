#!/usr/bin/env python3
"""
Karpathy Sequoia 포스트 추가 이미지 생성 스크립트 (4장)
실행: python3 scripts/gen-karpathy-sequoia-2.py

추가 생성:
  1. karpathy-sequoia-thinking-vs-understanding.webp  — 1번 본문 (hero 중복 해소)
  2. karpathy-sequoia-stripe-mapping.webp             — Stripe 이메일 매핑 일화
  3. karpathy-sequoia-one-on-one.webp                 — 원온원
  4. karpathy-sequoia-junior-growth.webp              — 주니어 성장
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
        "filename": "karpathy-sequoia-thinking-vs-understanding.webp",
        "size": "1536x1024",
        "prompt": (
            "Editorial illustration in muted earthy palette — beige, deep navy, rust. "
            "A close overhead shot of two open notebooks lying side by side on a dark walnut desk. "
            "The left notebook is filled with neat machine-generated print text glowing faintly. "
            "The right notebook is filled with messy hand-written ink notes, doodles, arrows, and crossed-out lines. "
            "A single warm lamp on the side. Small coffee cup in the corner. "
            "Photorealistic still life, cinematic, magazine spread feel. No readable text. "
            "Composition emphasizes the contrast between machine output and human thinking."
        ),
    },
    {
        "filename": "karpathy-sequoia-stripe-mapping.webp",
        "size": "1536x1024",
        "prompt": (
            "Editorial illustration — two glowing envelope icons floating in mid-air against a soft beige "
            "and deep navy background. Faint connecting lines try to match them but the lines tangle and split "
            "into four diverging paths labeled with abstract symbols (no readable text). "
            "A blurred human silhouette stands behind them holding a magnifying glass, considering which path. "
            "Muted painterly palette, photorealistic finish, contemplative mood. No readable text or logos."
        ),
    },
    {
        "filename": "karpathy-sequoia-one-on-one.webp",
        "size": "1536x1024",
        "prompt": (
            "Editorial scene — two people sitting at a small wooden round table by a large window, "
            "evening city light outside. Two coffee cups. Between them on the table floats a soft translucent "
            "holographic dashboard showing abstract bar charts and timeline blocks, glowing gently. "
            "Both are leaning in, engaged in conversation, not looking at the dashboard but at each other. "
            "Muted beige and navy palette, warm lamp light. Photorealistic editorial style, "
            "no readable text, no logos. Mood: thoughtful, intimate."
        ),
    },
    {
        "filename": "karpathy-sequoia-junior-growth.webp",
        "size": "1536x1024",
        "prompt": (
            "Editorial illustration — a young developer in a hoodie sits at a clean wooden desk in a warm-lit room, "
            "facing five floating translucent screens arranged in a fan around them. Each screen shows different "
            "abstract content — a graph, a 3D model, a code snippet, a design canvas, a data table — glowing softly. "
            "The developer is holding a sketchbook and pencil, not typing. Sketching a decision tree. "
            "Muted beige, deep navy, soft rust accents. Photorealistic with painterly finish. "
            "No readable text, no logos. Mood: focused, optimistic."
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
