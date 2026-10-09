from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.products import get_search_service
from app.database.database import get_db
from app.errors import AppError
from app.schemas.product import SearchResponse, TextSearchRequest
from app.services.product_service import ProductFilters
from app.services.search_service import SearchService
from app.utils.image_utils import prepare_for_model, read_limited, validate_image

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("/image", response_model=SearchResponse)
def search_image(
    image: UploadFile = File(...),
    top_k: int = Form(5, ge=1, le=20),
    category: str | None = Form(None),
    material: str | None = Form(None),
    purity: str | None = Form(None),
    occasion: str | None = Form(None),
    min_price: float | None = Form(None, ge=0),
    max_price: float | None = Form(None, ge=0),
    db: Session = Depends(get_db),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    # The upload is read into memory, validated and discarded.
    pil_image = validate_image(read_limited(image.file))

    filters = ProductFilters.clean(
        category=category,
        material=material,
        purity=purity,
        occasion=occasion,
        min_price=min_price,
        max_price=max_price,
    )

    results = service.search_by_image(
        db,
        prepare_for_model(pil_image),
        top_k,
        filters,
    )

    if not results:
        return SearchResponse(
            query_type="image",
            results=[],
            total=0,
            message="No sufficiently similar jewellery found.",
        )

    return SearchResponse(
        query_type="image",
        results=results,
        total=len(results),
    )


@router.post("/text", response_model=SearchResponse)
def search_text(
    body: TextSearchRequest,
    db: Session = Depends(get_db),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    filters = ProductFilters.clean(
        category=body.category,
        material=body.material,
        purity=body.purity,
        occasion=body.occasion,
        min_price=body.min_price,
        max_price=body.max_price,
    )

    results = service.search_by_text(
        db,
        body.text.strip(),
        body.top_k,
        filters,
    )

    return SearchResponse(
        query_type="text",
        results=results,
        total=len(results),
    )


@router.post("/hybrid", response_model=SearchResponse)
def search_hybrid(
    image: UploadFile | None = File(None),
    text: str | None = Form(None, max_length=200),
    top_k: int = Form(5, ge=1, le=20),
    image_weight: float | None = Form(None, ge=0),
    text_weight: float | None = Form(None, ge=0),
    category: str | None = Form(None),
    material: str | None = Form(None),
    purity: str | None = Form(None),
    occasion: str | None = Form(None),
    min_price: float | None = Form(None, ge=0),
    max_price: float | None = Form(None, ge=0),
    db: Session = Depends(get_db),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    pil_image = None

    if image is not None and image.filename:
        pil_image = prepare_for_model(
            validate_image(read_limited(image.file))
        )

    if pil_image is None and not (text and text.strip()):
        raise AppError(
            "INVALID_REQUEST",
            "Provide an image, a text query, or both.",
            400,
        )

    filters = ProductFilters.clean(
        category=category,
        material=material,
        purity=purity,
        occasion=occasion,
        min_price=min_price,
        max_price=max_price,
    )

    results = service.search_hybrid(
        db,
        pil_image,
        text,
        top_k,
        filters,
        image_weight,
        text_weight,
    )

    return SearchResponse(
        query_type="hybrid",
        results=results,
        total=len(results),
    )