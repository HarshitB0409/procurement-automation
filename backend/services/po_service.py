import uuid
from datetime import datetime

from fastapi import HTTPException

from models import GenericStepResponse, POLineItem, PurchaseOrder, ThreeWayMatchResult, VendorScore
from services.request_store import get_request, update_request


def generate_po_for_request(request_id: str) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status not in ("approved", "auto_approved"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate PO for status '{req.status}'",
        )

    raw_scores = req.vendor_scores or []
    scores = [VendorScore(**s) if isinstance(s, dict) else s for s in raw_scores]
    top = scores[0] if scores else None
    vendor_name = top.vendor_name if top else "Unknown Vendor"
    unit_price = (top.price / req.quantity) if top and req.quantity else req.cost / max(req.quantity, 1)
    line_total = top.price if top else req.cost

    po = PurchaseOrder(
        number=f"PO-{uuid.uuid4().hex[:8].upper()}",
        vendor_name=vendor_name,
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
        {"po": po.model_dump(), "status": "po_generated"},
    )
    return GenericStepResponse(
        request_id=request_id,
        status="po_generated",
        message=f"PO {po.number} generated",
        data={"po": po.model_dump()},
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
