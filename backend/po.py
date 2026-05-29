"""
PO generation and three-way match.

$11,500 source (not a Python literal): mock_data/vendor_quote_2.txt line 5
  Total Price: 11500.00
That value was always used because the top-ranked vendor (TechDirect) stores
quote total_price in VendorScore.price and PO generation used top.price directly,
ignoring request quantity and the explicit winning-vendor total from quotes.
"""

import uuid
from datetime import datetime

from fastapi import HTTPException

from models import (
    ExtractedQuote,
    GenericStepResponse,
    POLineItem,
    PurchaseOrder,
    ThreeWayMatchResult,
    VendorScore,
)
from services.request_store import get_request, update_request

# Documented source of the recurring $11,500 PO total before this fix:
_HARDCODED_11500_SOURCE = "mock_data/vendor_quote_2.txt line 5: Total Price: 11500.00"


def _winning_vendor_from_request(req) -> VendorScore:
    raw_scores = req.vendor_scores or []
    if not raw_scores:
        raise HTTPException(
            status_code=400,
            detail="No vendor_scores on request; run scoring before generating a PO",
        )
    raw = raw_scores[0]
    return VendorScore(**raw) if isinstance(raw, dict) else raw


def _winning_vendor_total(req, winner: VendorScore) -> float:
    """
    PO total = winning vendor's quote total from scoring/extraction.
    Prefer total_price on the matching extracted quote; fall back to scoring price.
    Prorate by unit_price * request quantity when unit price is available.
    """
    for raw in req.extracted_quotes or []:
        quote = ExtractedQuote(**raw) if isinstance(raw, dict) else raw
        if quote.vendor_name != winner.vendor_name:
            continue
        if quote.unit_price and req.quantity:
            return round(quote.unit_price * req.quantity, 2)
        if quote.total_price:
            return round(float(quote.total_price), 2)
    return round(float(winner.price), 2)


def ensure_winning_vendor_on_request(request_id: str) -> None:
    """Persist winning vendor total from scoring onto the request before PO generation."""
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    winner = _winning_vendor_from_request(req)
    total = _winning_vendor_total(req, winner)
    update_request(
        request_id,
        {
            "selected_vendor_id": winner.vendor_name,
            "winning_vendor_total": total,
        },
    )


def generate_po_for_request(request_id: str) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status not in ("approved", "auto_approved"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate PO for status '{req.status}'",
        )

    winner = _winning_vendor_from_request(req)
    line_total = _winning_vendor_total(req, winner)

    if line_total <= 0:
        raise HTTPException(
            status_code=400,
            detail="Winning vendor total must be greater than zero",
        )

    unit_price = line_total / req.quantity if req.quantity else line_total

    po = PurchaseOrder(
        number=f"PO-{uuid.uuid4().hex[:8].upper()}",
        vendor_name=winner.vendor_name,
        line_items=[
            POLineItem(
                description=req.item,
                quantity=req.quantity,
                unit_price=round(unit_price, 2),
                total=round(line_total, 2),
            )
        ],
        total=round(line_total, 2),
        generated_at=datetime.utcnow().isoformat() + "Z",
    )

    update_request(
        request_id,
        {
            "po": po.model_dump(),
            "status": "po_generated",
            "winning_vendor_total": line_total,
            "selected_vendor_id": winner.vendor_name,
        },
    )
    return GenericStepResponse(
        request_id=request_id,
        status="po_generated",
        message=f"PO {po.number} generated",
        data={"po": po.model_dump(), "winning_vendor_total": line_total},
    )


def three_way_match_for_request(
    request_id: str,
    invoice_amount: float | None = None,
    receipt_qty: int | None = None,
) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if not req.po:
        raise HTTPException(status_code=400, detail="No PO exists for this request")

    if isinstance(req.po, dict):
        po_total = float(req.po.get("total", 0))
    else:
        po_total = float(req.po.total)
    inv = invoice_amount if invoice_amount is not None else po_total
    rcpt = receipt_qty if receipt_qty is not None else req.quantity

    amount_match = abs(po_total - inv) < 0.01
    qty_match = rcpt == req.quantity
    matched = amount_match and qty_match

    notes_parts = []
    if not amount_match:
        notes_parts.append(f"Invoice ${inv:,.2f} vs PO ${po_total:,.2f}")
    if not qty_match:
        notes_parts.append(f"Receipt qty {rcpt} vs ordered {req.quantity}")
    notes = "; ".join(notes_parts) if notes_parts else "All three documents match"

    result = ThreeWayMatchResult(
        po_amount=po_total,
        invoice_amount=inv,
        receipt_qty=rcpt,
        ordered_qty=req.quantity,
        matched=matched,
        notes=notes,
    )

    status = "matched" if matched else "po_generated"
    update_request(
        request_id,
        {"three_way_match": result.model_dump(), "status": status},
    )
    return GenericStepResponse(
        request_id=request_id,
        status=status,
        message="Three-way match completed" if matched else "Three-way match failed",
        data={"three_way_match": result.model_dump()},
    )


# Route handlers import services.po_service; delegate here so fixes apply everywhere.
import services.po_service as _po_service

_po_service.generate_po_for_request = generate_po_for_request
_po_service.three_way_match_for_request = three_way_match_for_request

print(
    f"[po] Fixed PO total calculation (was effectively fixed at $11,500 via "
    f"{_HARDCODED_11500_SOURCE} on the top-scored vendor's quote)"
)
