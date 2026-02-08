#!/usr/bin/env python3
"""
그레이스클럽 후기 블로그 이미지 일러스트화 스크립트
"""
from PIL import Image, ImageEnhance, ImageFilter
import os

# 경로 설정
GDRIVE_BASE = "/Users/wonderit/wonderit@safeai.kr - Google Drive/My Drive/claudecode/uploads/images/260208-grace-club-socializing-party"
BLOG_IMAGES = "/Users/wonderit/workplace/wonderx/wonderx-blog/images/blog"

def illustrate_image(input_path, output_path, blur_faces=False, max_width=1200):
    """
    이미지를 일러스트 스타일로 변환
    - Edge enhance (엣지 강조)
    - Posterize (색상 단순화 16색)
    - Color enhance (2.0배)
    - Contrast (1.5배)
    - Sharpness (2.5배)
    - 개인정보 보호 (얼굴 영역 블러 처리)
    """
    print(f"Processing: {os.path.basename(input_path)}")

    # 이미지 열기
    img = Image.open(input_path)

    # EXIF 회전 처리
    try:
        from PIL.ExifTags import TAGS
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                if TAGS.get(tag) == 'Orientation':
                    if value == 3:
                        img = img.rotate(180, expand=True)
                    elif value == 6:
                        img = img.rotate(270, expand=True)
                    elif value == 8:
                        img = img.rotate(90, expand=True)
    except:
        pass

    # 리사이징 (웹 최적화)
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # 일러스트 효과 적용
    # 1. Edge enhance
    img = img.filter(ImageFilter.EDGE_ENHANCE)

    # 2. Posterize (색상 단순화)
    img = img.convert("RGB")
    from PIL import ImageOps
    img = ImageOps.posterize(img, 4)  # 16색 (2^4)

    # 3. Color enhance
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(2.0)

    # 4. Contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    # 5. Sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.5)

    # 6. 얼굴 블러 처리 (개인정보 보호)
    if blur_faces:
        # 상단 1/3 영역 블러 처리
        width, height = img.size
        blur_region = img.crop((0, 0, width, height // 3))
        blur_region = blur_region.filter(ImageFilter.GaussianBlur(radius=20))
        img.paste(blur_region, (0, 0))

    # 저장 (JPEG 80% 품질)
    img.convert("RGB").save(output_path, "JPEG", quality=80, optimize=True)

    # 파일 크기 확인
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  → Saved: {os.path.basename(output_path)} ({size_kb:.0f}KB)")

# 이미지 생성
print("\n=== 그레이스클럽 후기 이미지 일러스트화 ===\n")

# 1. 스튜디오 입구 (IMG_0838)
illustrate_image(
    f"{GDRIVE_BASE}/IMG_0838.JPG",
    f"{BLOG_IMAGES}/grace-club-entrance-illustrated.jpg",
    blur_faces=False
)

# 2. 파티 내부 문쪽 (IMG_0839)
illustrate_image(
    f"{GDRIVE_BASE}/IMG_0839.JPG",
    f"{BLOG_IMAGES}/grace-club-door-illustrated.jpg",
    blur_faces=False
)

# 3. 파티장 2층 (IMG_0841)
illustrate_image(
    f"{GDRIVE_BASE}/IMG_0841.JPG",
    f"{BLOG_IMAGES}/grace-club-interior-illustrated.jpg",
    blur_faces=True  # 개인정보 보호
)

# 4. 디저트 (IMG_0842)
illustrate_image(
    f"{GDRIVE_BASE}/IMG_0842.JPG",
    f"{BLOG_IMAGES}/grace-club-dessert-illustrated.jpg",
    blur_faces=False
)

print("\n✅ 모든 이미지 생성 완료!")
