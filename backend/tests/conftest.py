import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import text

from app.database.database import SessionLocal
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # runs the startup (lifespan) code
        yield c


@pytest.fixture(scope="session")
def db_available() -> bool:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def health(client) -> dict:
    return client.get("/api/v1/health").json()


@pytest.fixture
def require_db(db_available):
    if not db_available:
        pytest.skip("PostgreSQL is not reachable (check DATABASE_URL)")


@pytest.fixture
def require_full_stack(health):
    if not (health["database"] and health["ai_model"] and health["faiss_index"]):
        pytest.skip("needs PostgreSQL + OpenCLIP + FAISS index (run migrations, seed, create_index)")


def make_image_bytes(fmt: str = "PNG", size=(64, 64), color=(200, 160, 40)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, fmt)
    return buf.getvalue()


@pytest.fixture
def png_bytes() -> bytes:
    return make_image_bytes("PNG")
