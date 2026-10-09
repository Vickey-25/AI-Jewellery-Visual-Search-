"""Product queries and filter logic (all queries are parameterised by SQLAlchemy)."""
from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database.models import Product
from app.schemas.product import FacetsResponse, SearchResult, image_url_for


@dataclass(frozen=True)
class ProductFilters:
    category: str | None = None
    material: str | None = None
    purity: str | None = None
    occasion: str | None = None
    min_price: float | None = None
    max_price: float | None = None

    @classmethod
    def clean(cls, **kwargs) -> "ProductFilters":
        """Treat empty strings and zero price values as 'no filter'."""
        cleaned = {}

        for key, value in kwargs.items():
            if isinstance(value, str):
                value = value.strip() or None

            # Swagger may send 0.0 when the optional price field is left empty.
            # Treat zero as "no price filter".
            if key in ("min_price", "max_price") and value == 0:
                value = None

            cleaned[key] = value

        return cls(**cleaned)

    @property
    def active(self) -> bool:
        return any(v is not None for v in self.__dict__.values())


def apply_filters(stmt: Select, f: ProductFilters) -> Select:
    stmt = stmt.where(Product.is_active.is_(True))

    for column, value in (
        (Product.category, f.category),
        (Product.material, f.material),
        (Product.purity, f.purity),
        (Product.occasion, f.occasion),
    ):
        if value:
            stmt = stmt.where(func.lower(column) == value.lower())

    if f.min_price is not None:
        stmt = stmt.where(Product.price >= f.min_price)

    if f.max_price is not None:
        stmt = stmt.where(Product.price <= f.max_price)

    return stmt


def list_products(
    db: Session, page: int, limit: int, filters: ProductFilters
) -> tuple[list[Product], int]:
    base = apply_filters(select(Product), filters)

    total = db.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0

    items = db.scalars(
        base
        .order_by(Product.id)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return list(items), int(total)


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_facets(db: Session) -> FacetsResponse:
    def distinct(column) -> list[str]:
        stmt = select(column).where(
            Product.is_active.is_(True),
            column.is_not(None),
        )
        return sorted(db.scalars(stmt.distinct()).all())

    low, high = db.execute(
        select(
            func.min(Product.price),
            func.max(Product.price),
        ).where(Product.is_active.is_(True))
    ).one()

    return FacetsResponse(
        categories=distinct(Product.category),
        materials=distinct(Product.material),
        purities=distinct(Product.purity),
        occasions=distinct(Product.occasion),
        min_price=low,
        max_price=high,
    )


def to_search_result(product: Product, score: float) -> SearchResult:
    return SearchResult(
        product_id=product.id,
        product_code=product.product_code,
        name=product.name,
        category=product.category,
        material=product.material,
        purity=product.purity,
        weight=product.weight,
        price=product.price,
        image_url=image_url_for(product.image_filename),
        similarity=round(max(0.0, min(1.0, score)), 4),
    )