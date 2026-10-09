"""Setup script for Real-Photo Evaluation System directories and ground truth files."""

import csv
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.database import SessionLocal
from app.database.models import Product

EVAL_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation"
REAL_PHOTOS_DIR = EVAL_DIR / "real_photos"
NO_MATCH_DIR = EVAL_DIR / "no_match"

CAT_DIR_MAP = {
    "Bracelet": "bracelets",
    "Earrings": "earrings",
    "Necklace": "necklaces",
    "Ring": "rings",
}


def setup_directories_and_ground_truth():
    # 1. Create directory structure
    REAL_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    for cat_folder in CAT_DIR_MAP.values():
        (REAL_PHOTOS_DIR / cat_folder).mkdir(parents=True, exist_ok=True)
    NO_MATCH_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        active_products = (
            db.query(Product)
            .filter(Product.is_active.is_(True))
            .order_by(Product.id)
            .all()
        )
        prod_by_code = {p.product_code: p for p in active_products}
        prod_by_cat = {}
        for p in active_products:
            prod_by_cat.setdefault(p.category, []).append(p)

        # 2. Build real_photo_ground_truth.csv
        gt_rows = []

        # Check existing expected.json if available
        expected_json = EVAL_DIR / "expected" / "expected.json"
        if expected_json.exists():
            with open(expected_json, "r", encoding="utf-8") as f:
                expected_map = json.load(f)

            for q_filename, code_list in expected_map.items():
                if not code_list:
                    continue
                main_code = code_list[0]
                prod = prod_by_code.get(main_code)
                if not prod:
                    continue

                # Copy/place query image into real_photos/ category subfolder
                src_img = EVAL_DIR / "queries" / q_filename
                cat_folder = CAT_DIR_MAP.get(prod.category, "rings")
                dest_img = REAL_PHOTOS_DIR / cat_folder / q_filename

                if src_img.exists() and not dest_img.exists():
                    try:
                        with Image.open(src_img) as img:
                            img.save(dest_img)
                    except Exception:
                        pass

                # Acceptable product IDs (for duplicates with identical content)
                acceptable_ids = [str(prod.id)]
                # Find duplicates with same name/image filename
                dups = [
                    str(p.id) for p in active_products
                    if p.image_filename == prod.image_filename and p.id != prod.id
                ]
                acceptable_ids.extend(dups)
                acceptable_str = "|".join(acceptable_ids)

                gt_rows.append({
                    "query_image": f"{cat_folder}/{q_filename}",
                    "category": prod.category,
                    "expected_product_id": prod.id,
                    "expected_product_code": prod.product_code,
                    "acceptable_product_ids": acceptable_str,
                })

        # Save real_photo_ground_truth.csv
        gt_csv_path = EVAL_DIR / "real_photo_ground_truth.csv"
        with open(gt_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "query_image",
                    "category",
                    "expected_product_id",
                    "expected_product_code",
                    "acceptable_product_ids",
                ],
            )
            writer.writeheader()
            for row in gt_rows:
                writer.writerow(row)

        print(f"Created {gt_csv_path} with {len(gt_rows)} ground truth rows.")

        # 3. Build sample non-jewellery images & no_match_ground_truth.csv
        no_match_items = [
            ("car.jpg", (50, 50, 60), "Automobile Sedan View"),
            ("shoe.jpg", (120, 80, 50), "Leather Footwear Shoe"),
            ("phone.jpg", (30, 30, 30), "Smartphone Device Glass"),
            ("tree.jpg", (40, 100, 40), "Outdoor Green Foliage Tree"),
            ("person.jpg", (180, 140, 120), "Human Portrait Casual Wear"),
            ("building.jpg", (100, 100, 110), "Architectural Concrete Wall"),
            ("food.jpg", (200, 120, 40), "Dish Food Plate Meal"),
        ]

        no_match_rows = []
        for filename, color, label in no_match_items:
            img_path = NO_MATCH_DIR / filename
            if not img_path.exists():
                img = Image.new("RGB", (400, 400), color=color)
                draw = ImageDraw.Draw(img)
                draw.rectangle([50, 50, 350, 350], outline=(200, 200, 200), width=4)
                draw.text((100, 180), label, fill=(255, 255, 255))
                img.save(img_path, "JPEG")

            no_match_rows.append({
                "query_image": filename,
                "expected_match": "NONE",
            })

        no_match_csv_path = EVAL_DIR / "no_match_ground_truth.csv"
        with open(no_match_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["query_image", "expected_match"])
            writer.writeheader()
            for row in no_match_rows:
                writer.writerow(row)

        print(f"Created {no_match_csv_path} with {len(no_match_rows)} non-jewellery rows.")
        print(f"Evaluation directory structure created at {EVAL_DIR}")

    finally:
        db.close()


if __name__ == "__main__":
    setup_directories_and_ground_truth()
