from fastapi import APIRouter

from models import GeneratePOBody, GenericStepResponse, ThreeWayMatchBody
from services.po_service import generate_po_for_request, three_way_match_for_request

router = APIRouter(tags=["po"])


@router.post("/generate-po", response_model=GenericStepResponse)
def generate_po(body: GeneratePOBody) -> GenericStepResponse:
    return generate_po_for_request(body.request_id)


@router.post("/three-way-match", response_model=GenericStepResponse)
def three_way_match(body: ThreeWayMatchBody) -> GenericStepResponse:
    return three_way_match_for_request(
        body.request_id,
        invoice_amount=body.invoice_amount,
        receipt_qty=body.receipt_qty,
    )
