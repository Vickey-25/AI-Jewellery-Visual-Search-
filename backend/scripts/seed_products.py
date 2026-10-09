"""Insert the demo catalogue into PostgreSQL. Safe to run repeatedly (skips existing codes)."""
import sys
from pathlib import Path

from sqlalchemy import select, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402
from app.database.database import SessionLocal  # noqa: E402
from app.database.models import Product  # noqa: E402
from demo_catalogue import CATALOGUE  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("Connected to PostgreSQL")
        existing = set(db.scalars(select(Product.product_code)).all())
        inserted = 0
        for item in CATALOGUE:
            if item["product_code"] in existing:
                continue
            fields = {k: v for k, v in item.items() if k != "variant"}
            db.add(Product(**fields, is_active=True))
            inserted += 1
            if not (settings.images_dir / item["image_filename"]).exists():
                print(f"  note: image missing for {item['product_code']}: {item['image_filename']}")
        db.commit()
        print(f"Inserted products successfully: {inserted} new, {len(existing)} already existed")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Seeding failed ({type(exc).__name__}). Check DATABASE_URL and run 'alembic upgrade head'.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
