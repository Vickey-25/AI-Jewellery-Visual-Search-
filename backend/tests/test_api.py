import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.faiss_index import FaissIndex
from app.config import settings
from app.database.database import get_db
from app.main import app
from tests.conftest import make_image_bytes


def _upload(client, data: bytes, name="query.png", ctype="image/png", **form):
    return client.post("/api/v1/search/image", files={"image": (name, data, ctype)}, data=form)


def _assert_error(resp, status: int, code: str):
    assert resp.status_code == status
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == code
    assert "Traceback" not in resp.text


# ---- no database / model required -------------------------------------------------
def test_health_shape(client):
    body = client.get("/api/v1/health").json()
    assert set(body) == {"status", "database", "ai_model", "faiss_index", "device"}


def test_invalid_image_rejected(client):
    _assert_error(_upload(client, b"not an image", "fake.jpg", "image/jpeg"), 400, "INVALID_IMAGE")


def test_unsupported_format_rejected(client):
    _assert_error(
        _upload(client, make_image_bytes("GIF"), "a.gif", "image/gif"), 415, "UNSUPPORTED_FORMAT"
    )


def test_large_image_rejected(client):
    too_big = b"\0" * (settings.max_image_bytes + 1)
    _assert_error(_upload(client, too_big), 413, "IMAGE_TOO_LARGE")


def test_missing_image_field_is_validation_error(client):
    resp = client.post("/api/v1/search/image", data={"top_k": 5})
    _assert_error(resp, 422, "VALIDATION_ERROR")


def test_top_k_above_maximum_rejected(client, png_bytes):
    _assert_error(_upload(client, png_bytes, top_k=21), 422, "VALIDATION_ERROR")


def test_missing_faiss_index(client, png_bytes, monkeypatch, tmp_path):
    service = app.state.search_service
    empty = FaissIndex(tmp_path / "nope.index", tmp_path / "nope.json")
    monkeypatch.setattr(service, "index", empty)
    _assert_error(_upload(client, png_bytes), 503, "FAISS_UNAVAILABLE")


def test_database_unavailable(client):
    bad = create_engine(
        "postgresql+psycopg://nobody@127.0.0.1:1/none", connect_args={"connect_timeout": 2}
    )
    Session = sessionmaker(bind=bad)

    def broken_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = broken_db
    try:
        _assert_error(client.get("/api/v1/products"), 503, "DATABASE_UNAVAILABLE")
    finally:
        app.dependency_overrides.clear()


# ---- need PostgreSQL + seeded data -------------------------------------------------
def test_products_list(client, require_db):
    body = client.get("/api/v1/products", params={"limit": 5}).json()
    assert body["page"] == 1 and body["limit"] == 5
    assert len(body["items"]) <= 5
    if body["items"]:
        item = body["items"][0]
        assert item["image_url"].startswith("/images/")


def test_products_filter_by_category(client, require_db):
    body = client.get("/api/v1/products", params={"category": "necklace"}).json()
    assert all(p["category"].lower() == "necklace" for p in body["items"])


def test_product_details_and_404(client, require_db):
    items = client.get("/api/v1/products", params={"limit": 1}).json()["items"]
    if not items:
        pytest.skip("no seeded products")
    pid = items[0]["id"]
    assert client.get(f"/api/v1/products/{pid}").json()["id"] == pid
    _assert_error(client.get("/api/v1/products/99999999"), 404, "PRODUCT_NOT_FOUND")


# ---- full integration: image -> OpenCLIP -> FAISS -> PostgreSQL ---------------------
def test_image_search_end_to_end(client, require_full_stack):
    items = client.get("/api/v1/products", params={"limit": 100}).json()["items"]
    target = next((p for p in items if (settings.images_dir / p["image_filename"]).is_file()), None)
    if target is None:
        pytest.skip("no product images on disk")
    data = (settings.images_dir / target["image_filename"]).read_bytes()

    resp = _upload(client, data, target["image_filename"], "image/jpeg", top_k=5)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["query_type"] == "image"
    assert 0 < len(body["results"]) <= 5
    for r in body["results"]:
        assert r["product_id"] > 0
        assert 0.0 <= r["similarity"] <= 1.0
        assert r["name"] and r["product_code"] and r["image_url"]
    # Searching with a catalogue image must return that product among top results with high similarity.
    assert target["id"] in [r["product_id"] for r in body["results"]]
    assert body["results"][0]["similarity"] > 0.98


def test_similar_products_excludes_self(client, require_full_stack):
    items = client.get("/api/v1/products", params={"limit": 1}).json()["items"]
    pid = items[0]["id"]
    body = client.get(f"/api/v1/products/{pid}/similar", params={"top_k": 5}).json()
    assert all(r["product_id"] != pid for r in body["results"])
    assert len(body["results"]) <= 5


def test_search_with_filters(client, require_full_stack):
    items = client.get("/api/v1/products", params={"limit": 1}).json()["items"]
    data = (settings.images_dir / items[0]["image_filename"]).read_bytes()
    resp = _upload(client, data, "q.jpg", "image/jpeg", category="Ring", top_k=10)
    assert resp.status_code == 200
    assert all(r["category"] == "Ring" for r in resp.json()["results"])


def test_text_search(client, require_full_stack):
    resp = client.post("/api/v1/search/text", json={"text": "gold necklace with ruby", "top_k": 5})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) <= 5
