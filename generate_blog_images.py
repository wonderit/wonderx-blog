import asyncio
from google import genai
from google.genai import types
from pathlib import Path

VERTEX_PROJECT = "safe-ai-430609"
VERTEX_LOCATION = "us-central1"
BLOG_IMG_DIR = Path("/Users/wonderit/workplace/wonderx/wonderx-blog/public/images/blog")

client = genai.Client(vertexai=True, project=VERTEX_PROJECT, location=VERTEX_LOCATION)

async def generate_image(prompt, filename):
    print(f"Generating {filename}...")
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                save_path = BLOG_IMG_DIR / filename
                save_path.write_bytes(part.inline_data.data)
                print(f"  Saved: {save_path} ({len(part.inline_data.data)} bytes)")
                return True
        print(f"  WARNING: No image data in response for {filename}")
        return False
    except Exception as e:
        print(f"  ERROR generating {filename}: {e}")
        return False

async def main():
    prompts = [
        ("A moody cinematic wide shot of a Seoul Korea winter night street scene near a restaurant district. Neon signs in Korean reflecting on wet pavement. Dark atmospheric Korean cityscape. Film grain aesthetic. No text overlay. No people faces visible. High quality photograph.", "after-date-1.png"),
        ("A cozy Korean shabu-shabu hot pot restaurant interior shot from above angle. Warm steam rising from bubbling broth in a copper pot, wooden chopsticks, colorful side dishes banchan arranged on a dark wooden table. Intimate warm lighting. No faces visible. Cinematic food photography. Film-like warm tones. High quality.", "after-date-2.png"),
        ("A stylish modern Korean cafe scene. A beautiful strawberry tart dessert on a dark marble table with two iced americano coffee cups in clear glasses. Warm ambient lighting from pendant lamps, beanbag sofa blurred in background. Artistic moody food photography. Cinematic color grading with warm tones. High quality photograph.", "after-date-3.png"),
        ("A solitary male figure seen from behind only, dark silhouette, walking down a quiet narrow Seoul alley at night in winter. Warm yellow street lamps casting long shadows on the ground. Cinematic melancholic mood. Film noir aesthetic. Blue and warm orange color grading. No face visible at all. High quality cinematic photograph.", "after-date-4.png"),
        ("An elegant Italian bistro restaurant interior in Seoul Korea. Candlelight dinner table setting with crystal wine glasses on crisp white tablecloth. Warm golden ambient lighting from wall sconces. Empty leather seats. Cinematic wide angle composition. Dark sophisticated romantic mood. No people present. High quality photograph.", "bistro-date-1.png"),
        ("Close-up artistic food photography of a beautifully plated Italian pasta dish aglio e olio style with a glass of deep red wine beside it. Soft warm bokeh restaurant lights in background. Rich warm color tones. Cinematic shallow depth of field. High quality photograph.", "bistro-date-2.png"),
        ("A late-night Korean cafe interior with a charming antique wooden vintage door as entrance. Warm amber ambient lighting. Glass display case showcasing elegant desserts, tarts and pastries. Cozy intimate atmosphere with exposed brick walls. Mix of vintage and modern aesthetic. No people present. High quality photograph.", "bistro-date-3.png"),
        ("A nighttime urban street scene in Munjeong-dong Seoul Korea. Closed small shops with softly lit Korean neon signs along the street. A single person silhouette walking away from camera back view only. Urban night photography style. Cinematic blue and warm orange color grading. Moody atmospheric composition. High quality photograph.", "bistro-date-4.png"),
    ]
    results = []
    for prompt, filename in prompts:
        result = await generate_image(prompt, filename)
        results.append((filename, result))
    print("\n=== Generation Results ===")
    sc = sum(1 for _, s in results if s)
    for fn, s in results:
        print(f"  {fn}: {'OK' if s else 'FAILED'}")
    print(f"\nTotal: {sc}/{len(results)} images generated successfully.")

asyncio.run(main())
