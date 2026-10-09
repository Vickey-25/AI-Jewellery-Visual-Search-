"""Import script for public real-world jewelry dataset (Hugging Face sidd707/jewelry-design-dataset).

Populates local PostgreSQL Product catalogue with real jewelry images and
copies images into backend/data/images/ for model embedding and search.
"""
import argparse
import csv
import os
import shutil
import sys
import zipfile
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from PIL import Image
from sqlalchemy import select, text

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database.database import SessionLocal
from app.database.models import Product

DATASET_URL = "https://huggingface.co/datasets/sidd707/jewelry-design-dataset/resolve/main/dataset.zip"

CATEGORY_MAP = {
    "bracelet": ("Bracelet", "BR"),
    "bracelets": ("Bracelet", "BR"),
    "earring": ("Earrings", "ER"),
    "earrings": ("Earrings", "ER"),
    "earring_best": ("Earrings", "ER"),
    "necklace": ("Necklace", "NK"),
    "necklaces": ("Necklace", "NK"),
    "ring": ("Ring", "RG"),
    "rings": ("Ring", "RG"),
    "ring_best": ("Ring", "RG"),
    "bangle": ("Bangle", "BG"),
    "bangles": ("Bangle", "BG"),
    "pendant": ("Pendant", "PD"),
    "pendants": ("Pendant", "PD"),
}

# Synthetic material & metadata presets for test dataset visualization
CATEGORY_DEFAULTS = {
    "Bracelet": {
        "material": "Gold", "purity": "22K", "price_min": 35000, "price_max": 95000,
        "weight_min": 10.0, "weight_max": 25.0, "occasions": ["Daily Wear", "Party", "Traditional"]
    },
    "Earrings": {
        "material": "Gold", "purity": "22K", "price_min": 15000, "price_max": 65000,
        "weight_min": 4.0, "weight_max": 14.0, "occasions": ["Traditional", "Party", "Wedding"]
    },
    "Necklace": {
        "material": "Gold", "purity": "22K", "price_min": 50000, "price_max": 180000,
        "weight_min": 20.0, "weight_max": 50.0, "occasions": ["Wedding", "Traditional", "Party"]
    },
    "Ring": {
        "material": "Diamond", "purity": "18K", "price_min": 25000, "price_max": 120000,
        "weight_min": 3.5, "weight_max": 8.5, "occasions": ["Engagement", "Daily Wear", "Party"]
    },
    "Bangle": {
        "material": "Gold", "purity": "22K", "price_min": 45000, "price_max": 110000,
        "weight_min": 15.0, "weight_max": 35.0, "occasions": ["Traditional", "Wedding"]
    },
    "Pendant": {
        "material": "Gold", "purity": "18K", "price_min": 18000, "price_max": 55000,
        "weight_min": 3.0, "weight_max": 10.0, "occasions": ["Daily Wear", "Party"]
    }
}


def download_dataset_if_needed(target_dir: Path) -> Path:
    """Download and extract dataset.zip from Hugging Face if target_dir is missing or empty."""
    target_dir.mkdir(parents=True, exist_ok=True)
    if any(target_dir.iterdir()):
        return target_dir

    print(f"Dataset directory '{target_dir}' is empty. Downloading dataset from Hugging Face...")
    public_data_dir = target_dir.parent
    public_data_dir.mkdir(parents=True, exist_ok=True)
    zip_path = public_data_dir / "dataset.zip"

    if not zip_path.exists():
        print(f"Downloading {DATASET_URL} (405 MB)...")
        urllib.request.urlretrieve(DATASET_URL, zip_path)
        print("Download complete.")

    print(f"Extracting dataset into {target_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(target_dir)
    print("Extraction complete.")
    return target_dir


def discover_category_and_files(source_dir: Path) -> Tuple[List[Tuple[Path, str, str]], Optional[Path]]:
    """Recursively discover image files and their categories from directory structure."""
    discovered: List[Tuple[Path, str, str]] = []
    labels_csv: Optional[Path] = None

    # Search for dataset_labels.csv if available
    for csv_candidate in source_dir.rglob("dataset_labels.csv"):
        labels_csv = csv_candidate
        break

    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}

    for root_str, _, files in os.walk(source_dir):
        root_path = Path(root_str)
        folder_name = root_path.name.lower()

        cat_info = CATEGORY_MAP.get(folder_name)
        if not cat_info:
            continue

        cat_name, sku_prefix = cat_info
        for f in sorted(files):
            f_path = root_path / f
            if f_path.suffix.lower() in valid_exts and f_path.name != "dataset_labels.csv":
                discovered.append((f_path, cat_name, sku_prefix))

    return discovered, labels_csv


def load_descriptions_csv(csv_path: Optional[Path]) -> Dict[str, str]:
    """Load text descriptions from dataset_labels.csv if present."""
    descriptions: Dict[str, str] = {}
    if not csv_path or not csv_path.exists():
        return descriptions

    try:
        with open(csv_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                img_path = row.get("image_path", "").strip()
                desc = row.get("description", "").strip()
                if img_path and desc:
                    norm_key = os.path.basename(img_path).lower()
                    descriptions[norm_key] = desc
    except Exception as exc:
        print(f"Note: Could not parse {csv_path}: {exc}")

    return descriptions


def validate_image_file(file_path: Path) -> bool:
    """Validate that file is a readable, non-corrupted image."""
    try:
        if file_path.stat().st_size < 100 or file_path.stat().st_size > 20 * 1024 * 1024:
            return False
        with Image.open(file_path) as img:
            img.verify()
        # Verify can be called only once per Image object open, test reopening
        with Image.open(file_path) as img:
            img.load()
            if img.width < 10 or img.height < 10:
                return False
        return True
    except Exception:
        return False


def import_dataset(
    source_dir: Path,
    limit: int = 1000,
    replace_demo: bool = False,
    auto_download: bool = False,
) -> int:
    """Import public jewelry images into local backend image storage and PostgreSQL database."""
    if auto_download or not source_dir.exists() or not any(source_dir.iterdir()):
        source_dir = download_dataset_if_needed(source_dir)

    print(f"Scanning source directory: {source_dir}")
    discovered, csv_path = discover_category_and_files(source_dir)
    descriptions = load_descriptions_csv(csv_path)

    total_discovered = len(discovered)

    settings.images_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))

        if replace_demo:
            demo_codes = ["NK001", "NK002", "NK003", "NK004", "RG001", "RG002", "RG003", "RG004",
                          "ER001", "ER002", "ER003", "ER004", "BR001", "BR002", "BR003", "BR004",
                          "BG001", "BG002", "BG003", "BG004", "PD001", "PD002", "PD003", "PD004"]
            deactivated = db.query(Product).filter(Product.product_code.in_(demo_codes)).update(
                {"is_active": False}, synchronize_session=False
            )
            db.commit()
            print(f"Deactivated {deactivated} demo products.")

        existing_codes = set(db.scalars(select(Product.product_code)).all())
        existing_filenames = set(db.scalars(select(Product.image_filename)).all())

        imported = 0
        skipped = 0
        duplicates = 0
        invalid_count = 0
        category_counts: Dict[str, int] = {}

        # Round-robin category balance if limit is applied
        if limit > 0 and len(discovered) > limit:
            by_cat: Dict[str, List[Tuple[Path, str, str]]] = {}
            for item in discovered:
                by_cat.setdefault(item[1], []).append(item)
            
            balanced_items: List[Tuple[Path, str, str]] = []
            max_len = max(len(v) for v in by_cat.values()) if by_cat else 0
            for idx in range(max_len):
                for cat in sorted(by_cat.keys()):
                    if idx < len(by_cat[cat]):
                        balanced_items.append(by_cat[cat][idx])
                        if len(balanced_items) >= limit:
                            break
                if len(balanced_items) >= limit:
                    break
            items_to_process = balanced_items
        else:
            items_to_process = discovered[:limit] if limit > 0 else discovered

        cat_sku_counters: Dict[str, int] = {}

        for file_path, cat_name, sku_prefix in items_to_process:
            if not validate_image_file(file_path):
                invalid_count += 1
                continue

            current_count = cat_sku_counters.get(sku_prefix, 0) + 1
            cat_sku_counters[sku_prefix] = current_count

            # Find next available code
            code = f"HF-{sku_prefix}-{current_count:06d}"
            while code in existing_codes:
                current_count += 1
                cat_sku_counters[sku_prefix] = current_count
                code = f"HF-{sku_prefix}-{current_count:06d}"

            # Target filename in backend/data/images
            ext = file_path.suffix.lower()
            target_filename = f"hf_{sku_prefix.lower()}_{current_count:06d}{ext}"
            if target_filename in existing_filenames:
                duplicates += 1
                continue

            target_path = settings.images_dir / target_filename
            shutil.copy2(file_path, target_path)

            # Metadata creation
            orig_name = file_path.name.lower()
            dataset_desc = descriptions.get(orig_name, f"Real-world {cat_name.lower()} item from Hugging Face dataset.")
            full_desc = f"{dataset_desc} [Test metadata - Hugging Face dataset sidd707/jewelry-design-dataset]"

            defaults = CATEGORY_DEFAULTS.get(cat_name, CATEGORY_DEFAULTS["Bracelet"])
            
            # Deterministic price calculation based on filename hash
            fn_hash = sum(ord(c) for c in file_path.name)
            price_range = defaults["price_max"] - defaults["price_min"]
            price = float(defaults["price_min"] + (fn_hash % 100) * (price_range / 100.0))
            price = round(price / 100.0) * 100.0  # round to hundreds

            weight_range = defaults["weight_max"] - defaults["weight_min"]
            weight = float(round(defaults["weight_min"] + (fn_hash % 50) * (weight_range / 50.0), 2))

            occasion = defaults["occasions"][fn_hash % len(defaults["occasions"])]
            material = defaults["material"]
            purity = defaults["purity"]
            
            title_part = dataset_desc.split(".")[0][:60].strip()
            name = f"{cat_name} - {title_part}" if title_part else f"Real {cat_name} {code}"

            product = Product(
                product_code=code,
                name=name[:190],
                description=full_desc,
                category=cat_name,
                material=material,
                purity=purity,
                weight=weight,
                price=price,
                stone_type="Diamond" if material == "Diamond" else ("Ruby" if fn_hash % 3 == 0 else None),
                colour="Gold" if material == "Gold" else "Silver",
                occasion=occasion,
                image_filename=target_filename,
                is_active=True,
            )

            db.add(product)
            existing_codes.add(code)
            existing_filenames.add(target_filename)
            imported += 1
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

        db.commit()

        print("\nImport completed")
        print(f"Total discovered: {total_discovered}")
        print(f"Imported: {imported}")
        print(f"Skipped: {skipped}")
        print(f"Duplicates: {duplicates}")
        print(f"Invalid images: {invalid_count}")
        print("Categories:")
        for cat in sorted(category_counts.keys()):
            print(f"  {cat}s: {category_counts[cat]}" if not cat.endswith("s") else f"  {cat}: {category_counts[cat]}")

        return 0
    except Exception as exc:
        db.rollback()
        print(f"Import failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Hugging Face real jewelry dataset into Lumière PostgreSQL database.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent / "public-data" / "jewelry-design-dataset",
        help="Path to downloaded dataset directory",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum total products to import (default: 1000)",
    )
    parser.add_argument(
        "--replace-demo",
        action="store_true",
        help="Deactivate existing demo dataset products before importing",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Automatically download dataset zip from Hugging Face if source directory is missing",
    )

    args = parser.parse_args()
    return import_dataset(
        source_dir=args.source_dir,
        limit=args.limit,
        replace_demo=args.replace_demo,
        auto_download=args.download,
    )


if __name__ == "__main__":
    raise SystemExit(main())
