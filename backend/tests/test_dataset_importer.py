"""Tests for Hugging Face real dataset importer script and visual search verification."""

import pytest
from pathlib import Path
from PIL import Image

from scripts.import_public_jewelry_dataset import (
    CATEGORY_MAP,
    validate_image_file,
    import_dataset,
    discover_category_and_files,
)
from app.ai.faiss_index import FaissIndex
from app.config import settings
from app.database.database import SessionLocal
from app.database.models import Product


def test_category_mapping():
    assert CATEGORY_MAP["bracelet"] == ("Bracelet", "BR")
    assert CATEGORY_MAP["earring_best"] == ("Earrings", "ER")
    assert CATEGORY_MAP["necklace"] == ("Necklace", "NK")
    assert CATEGORY_MAP["ring_best"] == ("Ring", "RG")


def test_validate_image_file_valid_and_invalid(tmp_path):
    # Valid image
    valid_img_path = tmp_path / "test_valid.jpg"
    img = Image.new("RGB", (100, 100), color="gold")
    img.save(valid_img_path, format="JPEG")
    assert validate_image_file(valid_img_path) is True

    # Invalid corrupted file
    corrupt_path = tmp_path / "corrupt.jpg"
    corrupt_path.write_bytes(b"not an image file header")
    assert validate_image_file(corrupt_path) is False

    # Empty file
    empty_path = tmp_path / "empty.jpg"
    empty_path.write_bytes(b"")
    assert validate_image_file(empty_path) is False


def test_dataset_import_workflow(tmp_path, require_db):
    # Create mock dataset directory
    ds_dir = tmp_path / "mock_dataset"
    ring_dir = ds_dir / "ring_best"
    ring_dir.mkdir(parents=True)

    # Add 2 mock images
    for i in range(2):
        img_p = ring_dir / f"ring_{i}.jpg"
        img = Image.new("RGB", (120, 120), color=(200, 150, 50))
        img.save(img_p, "JPEG")

    res = import_dataset(source_dir=ds_dir, limit=5, replace_demo=False)
    assert res == 0

    # Verify database has imported items
    with SessionLocal() as db:
        imported = db.query(Product).filter(Product.product_code.like("HF-RG-%")).all()
        assert len(imported) >= 2


def test_duplicate_import_handling(tmp_path, require_db):
    ds_dir = tmp_path / "mock_dataset_dup"
    earring_dir = ds_dir / "earring_best"
    earring_dir.mkdir(parents=True)

    img_p = earring_dir / "earring_test.jpg"
    img = Image.new("RGB", (100, 100), color="silver")
    img.save(img_p, "JPEG")

    # Run importer twice
    import_dataset(source_dir=ds_dir, limit=5, replace_demo=False)
    # Re-run should skip duplicates smoothly
    res2 = import_dataset(source_dir=ds_dir, limit=5, replace_demo=False)
    assert res2 == 0


def test_faiss_index_mapping_integrity(require_full_stack):
    index = FaissIndex(settings.faiss_index_path, settings.faiss_mapping_path)
    assert index.load() is True
    assert index.size > 0
    assert len(index._ids) == index.size

    with SessionLocal() as db:
        active_count = db.query(Product).filter(Product.is_active.is_(True)).count()
        assert index.size <= active_count


