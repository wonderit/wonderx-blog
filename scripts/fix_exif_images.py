#!/usr/bin/env python3
"""
EXIF Orientation 자동 보정 스크립트

images/blog/ 폴더 내 모든 이미지의 EXIF Orientation 태그를 읽고,
회전이 필요한 경우 물리적으로 회전시킨 뒤 EXIF를 정리한다.

사용법:
  python3 scripts/fix_exif_images.py              # images/blog/ 전체
  python3 scripts/fix_exif_images.py path/to/img   # 특정 이미지/폴더
"""

import sys
import os
import glob
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow가 필요합니다: pip3 install Pillow")
    sys.exit(1)


def fix_exif_orientation(filepath: str) -> bool:
    """EXIF orientation을 적용하여 이미지를 정방향으로 저장한다.
    Returns True if the image was modified."""
    try:
        img = Image.open(filepath)

        # EXIF orientation 확인
        exif = img.getexif()
        orientation = exif.get(274)  # 274 = Orientation tag

        if orientation is None or orientation == 1:
            return False  # 이미 정방향

        # EXIF transpose 적용 (물리적 회전)
        original_size = img.size
        img_fixed = ImageOps.exif_transpose(img)

        if img_fixed is None:
            return False

        # 원본 포맷 유지
        fmt = img.format or Path(filepath).suffix.lstrip('.').upper()
        if fmt == 'JPG':
            fmt = 'JPEG'

        save_kwargs = {}
        if fmt == 'JPEG':
            save_kwargs['quality'] = 95
            save_kwargs['optimize'] = True
        elif fmt == 'PNG':
            save_kwargs['optimize'] = True

        img_fixed.save(filepath, format=fmt, **save_kwargs)

        new_size = img_fixed.size
        print(f"  [FIXED] {filepath}: EXIF orient={orientation}, "
              f"{original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
        return True

    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
        return False


def process_directory(directory: str) -> tuple:
    """디렉토리 내 모든 이미지를 처리한다."""
    extensions = ('*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG')
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, ext)))
        files.extend(glob.glob(os.path.join(directory, '**', ext), recursive=True))

    files = sorted(set(files))
    fixed = 0
    total = len(files)

    print(f"\n이미지 {total}개 스캔 중... ({directory})")
    print("-" * 60)

    for f in files:
        if fix_exif_orientation(f):
            fixed += 1

    return total, fixed


def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        # 기본: 블로그 이미지 폴더
        script_dir = Path(__file__).parent.parent
        target = str(script_dir / "images" / "blog")

    if os.path.isfile(target):
        print(f"\n단일 파일 처리: {target}")
        fixed = fix_exif_orientation(target)
        if not fixed:
            print("  이미 정방향이거나 EXIF 정보 없음")
    elif os.path.isdir(target):
        total, fixed = process_directory(target)
        print("-" * 60)
        print(f"완료: {total}개 스캔, {fixed}개 수정됨")
    else:
        print(f"파일/폴더를 찾을 수 없습니다: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
