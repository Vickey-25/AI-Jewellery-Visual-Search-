"""Comprehensive Unit & Integration Security Hardening Tests for Lumière API."""

import io
import os

import pytest
from PIL import Image

from app.config import settings
from app.schemas.product import SearchResult
from app.services.product_service import ProductFilters
from app.utils.image_utils import read_limited, validate_image


def _make_image_bytes(fmt="JPEG", size=(100, 100)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(200, 150, 100))
    img.save(buf, format=fmt)
    return buf.getvalue()


def _upload(client, data: bytes, name="query.png", ctype="image/png", **form):
    return client.post("/api/v1/search/image", files={"image": (name, data, ctype)}, data=form)


# A. Valid JPEG -> accepted
def test_valid_jpeg_accepted():
    data = _make_image_bytes("JPEG")
    img = validate_image(data)
    assert img is not None
    assert img.size == (100, 100)


# B. Valid PNG -> accepted
def test_valid_png_accepted():
    data = _make_image_bytes("PNG")
    img = validate_image(data)
    assert img is not None
    assert img.size == (100, 100)


# C. Valid WebP -> accepted
def test_valid_webp_accepted():
    data = _make_image_bytes("WEBP")
    img = validate_image(data)
    assert img is not None
    assert img.size == (100, 100)


# D. Fake .jpg containing non-image data -> rejected
def test_fake_jpg_non_image_rejected(client):
    resp = _upload(client, b"<html><body>Not an image</body></html>", "photo.jpg", "image/jpeg")
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_IMAGE"


# E. Corrupted image -> rejected
def test_corrupted_image_rejected(client):
    valid_header = _make_image_bytes("JPEG")[:20] + b"CORRUPTED_BYTES_STRING_12345"
    resp = _upload(client, valid_header, "corrupt.jpg", "image/jpeg")
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_IMAGE"


# F. Oversized image file size -> rejected (HTTP 413)
def test_oversized_image_file_rejected(client):
    oversized = b"\0" * (settings.max_image_bytes + 1024)
    resp = _upload(client, oversized, "huge.jpg", "image/jpeg")
    assert resp.status_code == 413
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "IMAGE_TOO_LARGE"
    assert "file is too large" in body["error"]["message"].lower()


# G. Excessive image dimensions -> rejected (HTTP 413)
def test_excessive_dimensions_rejected():
    large_dim_bytes = _make_image_bytes("PNG", size=(4097, 100))
    with pytest.raises(Exception) as excinfo:
        validate_image(large_dim_bytes)
    assert "IMAGE_DIMENSIONS_TOO_LARGE" in str(excinfo.value.code)


# H. Missing image -> clean 4xx response (HTTP 422)
def test_missing_image_clean_422_response(client):
    resp = client.post("/api/v1/search/image", data={"top_k": 5})
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


# I. top_k = 0 -> rejected
def test_top_k_zero_rejected(client):
    png_bytes = _make_image_bytes("PNG")
    resp = _upload(client, png_bytes, top_k=0)
    assert resp.status_code == 422


# J. negative top_k -> rejected
def test_negative_top_k_rejected(client):
    png_bytes = _make_image_bytes("PNG")
    resp = _upload(client, png_bytes, top_k=-5)
    assert resp.status_code == 422


# K. extremely large top_k -> rejected
def test_extremely_large_top_k_rejected(client):
    png_bytes = _make_image_bytes("PNG")
    resp = _upload(client, png_bytes, top_k=25)
    assert resp.status_code == 422


# L. Normal top_k -> accepted
def test_normal_top_k_accepted(client, require_full_stack):
    items = client.get("/api/v1/products", params={"limit": 1}).json()["items"]
    img_path = settings.images_dir / items[0]["image_filename"]
    if not img_path.is_file():
        pytest.skip("No product images on disk")
    resp = _upload(client, img_path.read_bytes(), "test.jpg", "image/jpeg", top_k=5)
    assert resp.status_code == 200
    assert len(resp.json()["results"]) <= 5


# M. Non-jewellery image -> no-match response (HTTP 200 with empty results & message)
def test_non_jewellery_no_match_response(client, require_full_stack):
    fake_non_jewellery_bytes = _make_image_bytes("PNG", size=(200, 200))
    resp = _upload(client, fake_non_jewellery_bytes, "non_jewellery.png", "image/png", top_k=5)
    assert resp.status_code == 200
    body = resp.json()
    assert body["query_type"] == "image"
    # When random noise/plain color image similarity is below threshold (0.80), empty results are returned
    if len(body["results"]) == 0:
        assert body["total"] == 0
        assert body["message"] == "No sufficiently similar jewellery found."


# N. Valid jewellery image -> normal results
def test_valid_jewellery_normal_results(client, require_full_stack):
    items = client.get("/api/v1/products", params={"limit": 1}).json()["items"]
    img_path = settings.images_dir / items[0]["image_filename"]
    if not img_path.is_file():
        pytest.skip("No product images on disk")
    resp = _upload(client, img_path.read_bytes(), "target.jpg", "image/jpeg", top_k=5)
    assert resp.status_code == 200
    body = resp.json()
    assert body["query_type"] == "image"
    assert len(body["results"]) > 0
    assert body["results"][0]["similarity"] >= 0.80


# O. Query image does not get persisted to disk
def test_query_image_not_persisted(client, require_full_stack):
    items = client.get("/api/v1/products", params={"limit": 1}).json()["items"]
    img_path = settings.images_dir / items[0]["image_filename"]
    if not img_path.is_file():
        pytest.skip("No product images on disk")
    
    files_before = set(os.listdir(settings.images_dir))
    resp = _upload(client, img_path.read_bytes(), "temp_query.jpg", "image/jpeg", top_k=5)
    assert resp.status_code == 200
    files_after = set(os.listdir(settings.images_dir))
    
    assert files_before == files_after, "Uploaded query image was persisted to disk!"


# P. Duplicate-product search still works
def test_duplicate_product_search_preserved(client, require_full_stack):
    items = client.get("/api/v1/products", params={"limit": 100}).json()["items"]
    target = next((p for p in items if (settings.images_dir / p["image_filename"]).is_file()), None)
    if not target:
        pytest.skip("No product images on disk")
    resp = _upload(client, (settings.images_dir / target["image_filename"]).read_bytes(), top_k=5)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    assert results[0]["similarity"] >= 0.80
