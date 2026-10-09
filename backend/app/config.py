"""Application settings, loaded once from environment variables / backend/.env."""
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

logger = logging.getLogger(__name__)


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (BACKEND_DIR / p).resolve()


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    try:
        val = os.getenv(name, "").strip()
        return int(val) if val.isdigit() else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str
    model_name: str
    model_pretrained: str
    model_device: str
    torch_num_threads: int | None
    faiss_index_path: Path
    faiss_mapping_path: Path
    images_dir: Path
    max_image_size_mb: float
    cors_origins: list[str]
    hybrid_image_weight: float
    hybrid_text_weight: float
    log_level: str
    visual_search_similarity_threshold: float = 0.80
    max_search_image_width: int = 4096
    max_search_image_height: int = 4096
    jwt_secret: str = "lumiere-ai-jewellery-secret-key-2026"
    jwt_algorithm: str = "HS256"

    @property
    def max_image_bytes(self) -> int:
        return int(self.max_image_size_mb * 1024 * 1024)


def load_settings() -> Settings:
    # No password in the fallback on purpose: set DATABASE_URL in backend/.env.
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        database_url = "postgresql+psycopg://postgres@localhost:5432/jewellery_ai"
        logger.warning("DATABASE_URL is not set. Copy .env.example to .env and set it.")
    threads = os.getenv("TORCH_NUM_THREADS", "").strip()
    return Settings(
        database_url=database_url,
        model_name=os.getenv("MODEL_NAME", "ViT-B-32"),
        model_pretrained=os.getenv("MODEL_PRETRAINED", "laion2b_s34b_b79k"),
        model_device=os.getenv("MODEL_DEVICE", "cpu"),
        torch_num_threads=int(threads) if threads.isdigit() else None,
        faiss_index_path=_path(os.getenv("FAISS_INDEX_PATH", "./data/index/jewellery.index")),
        faiss_mapping_path=_path(os.getenv("FAISS_MAPPING_PATH", "./data/index/id_mapping.json")),
        images_dir=_path(os.getenv("IMAGES_DIR", "./data/images")),
        max_image_size_mb=_float("MAX_IMAGE_SIZE_MB", 5.0),
        cors_origins=_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
        hybrid_image_weight=_float("HYBRID_IMAGE_WEIGHT", 0.6),
        hybrid_text_weight=_float("HYBRID_TEXT_WEIGHT", 0.4),
        visual_search_similarity_threshold=_float("VISUAL_SEARCH_SIMILARITY_THRESHOLD", 0.80),
        max_search_image_width=_int("MAX_SEARCH_IMAGE_WIDTH", 4096),
        max_search_image_height=_int("MAX_SEARCH_IMAGE_HEIGHT", 4096),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        jwt_secret=os.getenv("JWT_SECRET", "lumiere-ai-jewellery-secret-key-2026"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    )


settings = load_settings()
