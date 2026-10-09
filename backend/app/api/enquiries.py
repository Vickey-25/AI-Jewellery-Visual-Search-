from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_shopowner
from app.database.database import get_db
from app.database.models import Enquiry, User
from app.errors import AppError
from app.schemas.product import EnquiryListResponse, EnquiryOut, UpdateEnquiryStatusRequest

router = APIRouter(prefix="/api/v1/enquiries", tags=["enquiries"])


@router.get("", response_model=EnquiryListResponse)
def list_enquiries_for_owner(
    status: str | None = Query(None),
    search: str | None = Query(None),
    shopowner: User = Depends(require_shopowner),
    db: Session = Depends(get_db),
) -> EnquiryListResponse:
    """Retrieve all client enquiries for the shop owner, sorted newest first."""
    stmt = (
        select(Enquiry)
        .options(joinedload(Enquiry.product))
        .order_by(desc(Enquiry.created_at))
    )

    if status and status.lower() != "all":
        stmt = stmt.where(Enquiry.status == status.lower())

    enquiries = db.scalars(stmt).all()

    # Search filter in python if requested
    if search and search.strip():
        q = search.strip().lower()
        enquiries = [
            e for e in enquiries
            if (
                q in e.name.lower()
                or q in e.email.lower()
                or (e.phone and q in e.phone.lower())
                or (e.message and q in e.message.lower())
                or (e.product and (q in e.product.name.lower() or q in e.product.product_code.lower()))
            )
        ]

    return EnquiryListResponse(
        items=[EnquiryOut.model_validate(e) for e in enquiries],
        total=len(enquiries),
    )


@router.patch("/{enquiry_id}/status", response_model=EnquiryOut)
def update_enquiry_status(
    enquiry_id: int,
    data: UpdateEnquiryStatusRequest,
    shopowner: User = Depends(require_shopowner),
    db: Session = Depends(get_db),
) -> EnquiryOut:
    """Update status of a client enquiry (pending, contacted, completed, cancelled)."""
    enquiry = db.get(Enquiry, enquiry_id)
    if not enquiry:
        raise AppError("ENQUIRY_NOT_FOUND", "Enquiry record not found.", 404)

    enquiry.status = data.status
    db.commit()
    db.refresh(enquiry)
    return EnquiryOut.model_validate(enquiry)


@router.get("/my", response_model=EnquiryListResponse)
def list_customer_enquiries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnquiryListResponse:
    """Retrieve enquiries made by the logged-in customer."""
    stmt = (
        select(Enquiry)
        .options(joinedload(Enquiry.product))
        .where(
            (Enquiry.user_id == current_user.id)
            | (Enquiry.email == current_user.email)
        )
        .order_by(desc(Enquiry.created_at))
    )
    items = db.scalars(stmt).all()
    return EnquiryListResponse(
        items=[EnquiryOut.model_validate(e) for e in items],
        total=len(items),
    )
