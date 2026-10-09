import re
import uuid
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user, require_shopowner
from app.config import settings
from app.database.database import get_db
from app.database.models import Enquiry, Product, User
from app.errors import AppError
from app.schemas.product import (
    EnquiryRequest,
    EnquiryResponse,
    FacetsResponse,
    ProductListResponse,
    ProductOut,
    SearchResponse,
)
from app.services import product_service
from app.services.product_service import ProductFilters
from app.services.search_service import SearchService
from app.utils.image_utils import prepare_for_model, read_limited, validate_image

router = APIRouter(prefix="/api/v1", tags=["products"])


def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service


@router.get("/products", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    material: str | None = None,
    purity: str | None = None,
    occasion: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    filters = ProductFilters.clean(
        category=category,
        material=material,
        purity=purity,
        occasion=occasion,
        min_price=min_price,
        max_price=max_price,
    )
    items, total = product_service.list_products(db, page, limit, filters)
    return ProductListResponse(
        items=[ProductOut.model_validate(p) for p in items], page=page, limit=limit, total=total
    )


# Declared before /products/{product_id} so "facets" is not parsed as an id.
@router.get("/products/facets", response_model=FacetsResponse)
def product_facets(db: Session = Depends(get_db)) -> FacetsResponse:
    return product_service.get_facets(db)


def _get_or_404(db: Session, product_id: int):
    product = product_service.get_product(db, product_id)
    if product is None or not product.is_active:
        raise AppError("PRODUCT_NOT_FOUND", "Product not found.", 404)
    return product


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductOut:
    return ProductOut.model_validate(_get_or_404(db, product_id))


@router.get("/products/{product_id}/similar", response_model=SearchResponse)
def similar_products(
    product_id: int,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    _get_or_404(db, product_id)
    results = service.similar_to_product(db, product_id, top_k)
    return SearchResponse(query_type="similar", results=results, total=len(results))


@router.post("/products/{product_id}/enquire", response_model=EnquiryResponse)
def enquire_product(
    product_id: int,
    request: EnquiryRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> EnquiryResponse:
    _get_or_404(db, product_id)
    enquiry = Enquiry(
        product_id=product_id,
        user_id=current_user.id if current_user else None,
        name=request.name.strip(),
        email=request.email.strip().lower(),
        phone=request.phone.strip() if request.phone else None,
        status="pending",
        message=request.message.strip() if request.message else None,
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    return EnquiryResponse(
        success=True,
        message="Your enquiry has been received. Our master jeweller will get in touch with you shortly.",
        enquiry_id=enquiry.id,
    )


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    image: UploadFile = File(...),
    name: str = Form(..., min_length=2, max_length=200),
    category: str = Form(..., min_length=2, max_length=50),
    material: str = Form(..., min_length=2, max_length=50),
    price: float = Form(..., gt=0),
    product_code: str | None = Form(None),
    purity: str | None = Form(None),
    weight: float | None = Form(None),
    stone_type: str | None = Form(None),
    colour: str | None = Form(None),
    occasion: str | None = Form(None),
    description: str | None = Form(None),
    shopowner: User = Depends(require_shopowner),
    db: Session = Depends(get_db),
    service: SearchService = Depends(get_search_service),
) -> ProductOut:
    """Create a new jewellery item with photo, compute AI embedding, and index in FAISS."""
    # 1. Validate image in memory
    raw_bytes = read_limited(image.file)
    pil_image = validate_image(raw_bytes)

    # 2. Determine or auto-generate unique product_code
    if product_code and product_code.strip():
        code = product_code.strip().upper()
        existing = db.scalar(select(Product).where(Product.product_code == code))
        if existing:
            raise AppError("CODE_EXISTS", f"Product code '{code}' already exists.", 400)
    else:
        cat_prefix = category[:2].upper() if len(category) >= 2 else "JW"
        code = f"{cat_prefix}{uuid.uuid4().hex[:6].upper()}"

    # 3. Save sanitized image to backend/data/images
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", code).lower()
    filename = f"{slug}_{uuid.uuid4().hex[:6]}.jpg"
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    target_path = settings.images_dir / filename
    pil_image.save(target_path, "JPEG", quality=92)

    # 4. Insert into database
    product = Product(
        product_code=code,
        name=name.strip(),
        description=description.strip() if description else None,
        category=category.strip(),
        material=material.strip(),
        purity=purity.strip() if purity else None,
        weight=weight,
        price=price,
        stone_type=stone_type.strip() if stone_type else None,
        colour=colour.strip() if colour else None,
        occasion=occasion.strip() if occasion else None,
        image_filename=filename,
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # 5. Compute OpenCLIP embedding & add to FAISS index immediately
    if service.clip:
        try:
            prepared = prepare_for_model(pil_image)
            vector = service.clip.generate_image_embedding(prepared)
            service.index.add_single(vector, product.id)
        except Exception as e:
            # Vector indexing failure should not crash product creation
            import logging
            logging.getLogger(__name__).warning("Failed to index product %d in FAISS: %s", product.id, e)

    return ProductOut.model_validate(product)


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    shopowner: User = Depends(require_shopowner),
) -> dict:
    """Deactivate a jewellery piece from active catalogue."""
    product = _get_or_404(db, product_id)
    product.is_active = False
    db.commit()
    return {"success": True, "message": f"Product '{product.name}' has been deactivated."}
