"""Script to verify ground truth rows against PostgreSQL and populate acceptable_product_ids with verified visually identical catalog items."""

import csv
import hashlib
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database.database import SessionLocal
from app.database.models import Product

EVAL_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation"
GT_CSV_PATH = EVAL_DIR / "real_photo_ground_truth.csv"


def update_ground_truth_acceptable_ids():
    db = SessionLocal()
    try:
        active_products = (
            db.query(Product)
            .filter(Product.is_active.is_(True))
            .order_by(Product.id)
            .all()
        )
        prod_by_id = {p.id: p for p in active_products}

        # Build map of image content hash -> set of product IDs
        hash_to_ids = {}
        for p in active_products:
            if not p.image_filename:
                continue
            img_path = settings.images_dir / p.image_filename
            if img_path.is_file():
                h = hashlib.md5(img_path.read_bytes()).hexdigest()
                hash_to_ids.setdefault(h, set()).add(p.id)

        rows = []
        with open(GT_CSV_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exp_id_str = row.get("expected_product_id", "").strip()
                if not exp_id_str.isdigit():
                    rows.append(row)
                    continue

                exp_id = int(exp_id_str)
                prod = prod_by_id.get(exp_id)
                if not prod or not prod.image_filename:
                    rows.append(row)
                    continue

                img_path = settings.images_dir / prod.image_filename
                acceptable_set = {exp_id}
                if img_path.is_file():
                    h = hashlib.md5(img_path.read_bytes()).hexdigest()
                    acceptable_set.update(hash_to_ids.get(h, set()))

                # Format acceptable_product_ids sorted numerically
                sorted_ids = sorted(list(acceptable_set))
                row["acceptable_product_ids"] = "|".join(str(i) for i in sorted_ids)
                rows.append(row)

        with open(GT_CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "query_image",
                "category",
                "expected_product_id",
                "expected_product_code",
                "acceptable_product_ids",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        print(f"Successfully updated {len(rows)} rows in {GT_CSV_PATH} with acceptable_product_ids.")

    finally:
        db.close()


if __name__ == "__main__":
    update_ground_truth_acceptable_ids()
