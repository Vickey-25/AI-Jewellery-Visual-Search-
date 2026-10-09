from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


def image_url_for(filename: str | None) -> str | None:
    return f"/images/{filename}" if filename else None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_code: str
    name: str
    description: str | None = None
    category: str
    material: str
    purity: str | None = None
    weight: float | None = None
    price: float
    stone_type: str | None = None
    colour: str | None = None
    occasion: str | None = None
    image_filename: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def image_url(self) -> str | None:
        return image_url_for(self.image_filename)


class ProductListResponse(BaseModel):
    items: list[ProductOut]
    page: int
    limit: int
    total: int


class FacetsResponse(BaseModel):
    categories: list[str]
    materials: list[str]
    purities: list[str]
    occasions: list[str]
    min_price: float | None
    max_price: float | None


class SearchResult(BaseModel):
    product_id: int
    product_code: str
    name: str
    category: str
    material: str
    purity: str | None = None
    weight: float | None = None
    price: float
    image_url: str | None = None
    # Retrieval similarity score in [0, 1]. It is NOT a probability.
    similarity: float


class SearchResponse(BaseModel):
    query_type: str
    results: list[SearchResult]
    total: int
    message: str | None = None


class TextSearchRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    top_k: int = Field(5, ge=1, le=20)
    category: str | None = None
    material: str | None = None
    purity: str | None = None
    occasion: str | None = None
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)


class EnquiryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    phone: str | None = Field(None, max_length=50)
    message: str | None = Field(None, max_length=1000)


class EnquiryResponse(BaseModel):
    success: bool
    message: str
    enquiry_id: int | None = None


class EnquiryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    user_id: int | None = None
    name: str
    email: str
    phone: str | None = None
    status: str
    message: str | None = None
    created_at: datetime
    product: ProductOut | None = None


class EnquiryListResponse(BaseModel):
    items: list[EnquiryOut]
    total: int


class UpdateEnquiryStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|contacted|completed|cancelled)$")
