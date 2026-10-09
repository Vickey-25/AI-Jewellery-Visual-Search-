"""FastAPI application: routers, CORS, static images, error handling, startup."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.ai.faiss_index import FaissIndex
from app.api import auth, enquiries, products, search
from app.config import settings
from app.database.database import engine
from app.errors import AppError, error_body
from app.services.search_service import SearchService

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app")


def database_ok() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # never log the URL: it contains the password
        logger.warning("Database check failed: %s", type(exc).__name__)
        return False


def load_clip():
    """Load OpenCLIP once. If it fails, the API still starts and reports ai_model=false."""
    try:
        from app.ai.clip_service import CLIPService

        return CLIPService(
            settings.model_name,
            settings.model_pretrained,
            settings.model_device,
            settings.torch_num_threads,
        )
    except Exception:
        logger.exception("OpenCLIP failed to load")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ok = database_ok()
    clip = load_clip()
    index = FaissIndex(settings.faiss_index_path, settings.faiss_mapping_path)
    index.load()
    app.state.search_service = SearchService(
        clip, index, settings.hybrid_image_weight, settings.hybrid_text_weight
    )
    device = clip.device.upper() if clip else "UNKNOWN"
    logger.info(
        "\n========================================\n"
        "AI JEWELLERY VISUAL SEARCH\n"
        "========================================\n\n"
        "Database: %s\nAI Device: %s\nOpenCLIP: %s\nFAISS: %s\nAPI: Ready\n\n"
        "========================================",
        "Connected" if db_ok else "UNAVAILABLE",
        device,
        "Loaded" if clip else "NOT LOADED",
        f"Loaded ({index.size} vectors)" if index.loaded else "NOT LOADED (run scripts/create_index.py)",
    )
    yield
    engine.dispose()


app = FastAPI(title="AI Jewellery Visual Search", version="1.0.0", lifespan=lifespan)


# ---- error handling ---------------------------------------------------------------
def _json_error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content=error_body(code, message))


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return _json_error(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _json_error(422, "VALIDATION_ERROR", "Some request values are missing or invalid.")


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    return _json_error(exc.status_code, code, "The requested resource was not available.")


@app.exception_handler(OperationalError)
async def handle_db_error(_: Request, exc: OperationalError) -> JSONResponse:
    logger.warning("Database error: %s", type(exc).__name__)
    return _json_error(503, "DATABASE_UNAVAILABLE", "The product database is not available right now.")


# Registered before CORS so that even unexpected 500s pass through the CORS layer
# (otherwise the browser would hide the JSON error behind a CORS failure).
@app.middleware("http")
async def catch_unhandled(request: Request, call_next):
    try:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _json_error(500, "INTERNAL_ERROR", "Something went wrong. Please try again.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---- routes ------------------------------------------------------------------------
settings.images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=settings.images_dir), name="images")
app.include_router(auth.router)
app.include_router(enquiries.router)
app.include_router(products.router)
app.include_router(search.router)


@app.get("/api/v1/health", tags=["health"])
def health(request: Request) -> dict:
    service: SearchService = request.app.state.search_service
    service.index.refresh_if_changed()
    db_ok = database_ok()
    ai_ok = service.clip is not None
    index_ok = service.index.loaded
    return {
        "status": "ok" if (db_ok and ai_ok and index_ok) else "degraded",
        "database": db_ok,
        "ai_model": ai_ok,
        "faiss_index": index_ok,
        "device": service.clip.device if service.clip else None,
    }
