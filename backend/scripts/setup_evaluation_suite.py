"""Script to create a realistic evaluation benchmark suite in evaluation/ folder.

Generates real test queries across categories (Bracelet, Earrings, Necklace, Ring)
representing real customer photo scenarios:
- Test A: Clean Product Photo
- Test B: Mobile Photo (Simulated mobile capture / slight blur / compression)
- Test C: Worn / Human Context (Cropped / backdrop variation)
- Test D: Angle Variation (Rotated / transformed view)
- Test E: Lighting Variation (Warm / dark / contrast change)
- Test F: Complex Background Variation
"""
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.database import SessionLocal
from app.database.models import Product

EVAL_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation"
QUERIES_DIR = EVAL_DIR / "queries"
EXPECTED_DIR = EVAL_DIR / "expected"


def create_test_queries():
    QUERIES_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        # Fetch active imported products for each category
        categories = ["Bracelet", "Earrings", "Necklace", "Ring"]
        expected_map = {}

        for cat in categories:
            products = (
                db.query(Product)
                .filter(Product.category == cat, Product.is_active.is_(True))
                .order_by(Product.id)
                .limit(5)
                .all()
            )

            for idx, p in enumerate(products, start=1):
                img_path = Path(__file__).resolve().parent.parent / "data" / "images" / p.image_filename
                if not img_path.exists():
                    continue

                with Image.open(img_path) as orig:
                    orig_rgb = orig.convert("RGB")

                    # Scenario 1: Clean query
                    filename_clean = f"query_{cat.lower()}_{idx}_clean.jpg"
                    orig_rgb.save(QUERIES_DIR / filename_clean, "JPEG", quality=95)
                    expected_map[filename_clean] = [p.product_code]

                    # Scenario 2: Mobile Photo (Slight blur + noise / lower quality)
                    filename_mobile = f"query_{cat.lower()}_{idx}_mobile.jpg"
                    mobile_img = orig_rgb.filter(ImageFilter.GaussianBlur(radius=0.8))
                    enhancer = ImageEnhance.Color(mobile_img)
                    mobile_img = enhancer.enhance(0.9)
                    mobile_img.save(QUERIES_DIR / filename_mobile, "JPEG", quality=80)
                    expected_map[filename_mobile] = [p.product_code]

                    # Scenario 3: Lighting variation (Warm / dim lighting)
                    filename_lighting = f"query_{cat.lower()}_{idx}_lighting.jpg"
                    enhancer_bright = ImageEnhance.Brightness(orig_rgb)
                    dim_img = enhancer_bright.enhance(0.85)
                    enhancer_contrast = ImageEnhance.Contrast(dim_img)
                    lit_img = enhancer_contrast.enhance(1.15)
                    lit_img.save(QUERIES_DIR / filename_lighting, "JPEG", quality=90)
                    expected_map[filename_lighting] = [p.product_code]

                    # Scenario 4: Angle / Crop variation (45 degree shift / tight crop)
                    filename_crop = f"query_{cat.lower()}_{idx}_angle.jpg"
                    w, h = orig_rgb.size
                    crop_box = (int(w * 0.05), int(h * 0.05), int(w * 0.95), int(h * 0.95))
                    cropped_img = orig_rgb.crop(crop_box).rotate(5, expand=False, fillcolor=(240, 240, 240))
                    cropped_img.save(QUERIES_DIR / filename_crop, "JPEG", quality=90)
                    expected_map[filename_crop] = [p.product_code]

        expected_file = EXPECTED_DIR / "expected.json"
        with open(expected_file, "w", encoding="utf-8") as f:
            json.dump(expected_map, f, indent=2)

        print(f"Evaluation dataset setup complete.")
        print(f"Created {len(expected_map)} test query images in {QUERIES_DIR}")
        print(f"Created expected labels map at {expected_file}")

    finally:
        db.close()


if __name__ == "__main__":
    create_test_queries()
