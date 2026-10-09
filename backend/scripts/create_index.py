"""Build the FAISS index from the active products in PostgreSQL.

Run again whenever products or images change. A running API picks up the new index
automatically (no restart needed).
"""
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from sqlalchemy import select, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.ai.faiss_index import FaissIndex  # noqa: E402
from app.config import settings  # noqa: E402
from app.database.database import SessionLocal  # noqa: E402
from app.database.models import Product  # noqa: E402
from app.utils.image_utils import prepare_for_model  # noqa: E402


def main() -> int:
    print("Connecting to PostgreSQL...")
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        products = db.execute(
            select(Product.id, Product.product_code, Product.image_filename)
            .where(Product.is_active.is_(True))
            .order_by(Product.id)
        ).all()
    except Exception as exc:
        print(f"Could not read products ({type(exc).__name__}). Check PostgreSQL and DATABASE_URL.")
        return 1
    finally:
        db.close()

    print("Loading OpenCLIP...")
    from app.ai.clip_service import CLIPService

    clip = CLIPService(settings.model_name, settings.model_pretrained,
                       settings.model_device, settings.torch_num_threads)
    print(f"Device: {clip.device}\n")
    print(f"Products found: {len(products)}\n")
    if not products:
        print("No active products. Run scripts/seed_products.py first.")
        return 1

    print("Processing:")
    vectors: list[np.ndarray] = []
    ids: list[int] = []
    skipped: list[str] = []
    started = time.time()
    for n, (pid, code, filename) in enumerate(products, start=1):
        path = settings.images_dir / filename if filename else None
        if path is None or not path.is_file():
            print(f"{n}/{len(products)}  SKIPPED {code}: image file missing ({filename})")
            skipped.append(code)
            continue
        try:
            with Image.open(path) as raw:
                raw.load()
                prepared = prepare_for_model(raw)
            vectors.append(clip.generate_image_embedding(prepared))
            ids.append(pid)
            print(f"{n}/{len(products)}")
        except Exception as exc:
            print(f"{n}/{len(products)}  SKIPPED {code}: cannot read image ({type(exc).__name__})")
            skipped.append(code)

    if not vectors:
        print("\nNo embeddings were generated, so no index was written.")
        return 1

    index = FaissIndex(settings.faiss_index_path, settings.faiss_mapping_path)
    index.build(np.vstack(vectors), ids)
    print("\nFAISS index created successfully.")
    print(f"Products indexed: {len(ids)}  ({time.time() - started:.1f}s)")
    if skipped:
        print(f"Skipped (fix and re-run): {', '.join(skipped)}")
    print(f"Index: {settings.faiss_index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
