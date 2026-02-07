#!/usr/bin/env python3
"""ENFP CTO 캐릭터 이미지 생성"""

from PIL import Image
import google.generativeai as genai
import os
import io

# Gemini 설정
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

prompt = """
Generate a friendly, professional character illustration representing an ENFP CTO working at an AI startup.

Character details:
- Korean male in 30s
- Casual tech startup vibe (hoodie or casual shirt)
- Holding a laptop or tablet
- Surrounded by abstract AI/tech icons (circuit patterns, neural network lines, automation symbols)
- Warm, approachable expression
- Modern, clean illustration style
- Vibrant but professional color palette

Style: Modern flat illustration, minimalist but detailed, tech-forward aesthetic
Background: Subtle gradient or abstract tech pattern
Mood: Innovative, friendly, energetic but focused
"""

try:
    print("캐릭터 이미지 생성 중...")
    response = model.generate_content([prompt])

    # 이미지 생성은 Gemini 2.0 Flash가 지원하지 않음
    # Imagen 사용 필요
    print("Gemini 2.0 Flash는 이미지 생성을 지원하지 않습니다.")
    print("대신 Imagen 3 또는 외부 이미지 생성 도구를 사용하세요.")

except Exception as e:
    print(f"오류 발생: {e}")
