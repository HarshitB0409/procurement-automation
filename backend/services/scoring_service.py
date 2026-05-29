from models import ExtractedQuote, GenericStepResponse
from services.request_store import get_request, update_request
from services.scoring import compute_vendor_scores


def score_vendors_for_request(request_id: str) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        return GenericStepResponse(
            request_id=request_id,
            status="submitted",
            message="Request not found",
        )

    raw_quotes = req.extracted_quotes or []
    if not raw_quotes:
        return GenericStepResponse(
            request_id=request_id,
            status=req.status,
            message="No extracted quotes to score",
        )

    quotes = [
        ExtractedQuote(**q) if isinstance(q, dict) else q
        for q in raw_quotes
    ]

    scores = compute_vendor_scores(quotes)
    selected = scores[0].vendor_name if scores else None

    update_request(
        request_id,
        {
            "vendor_scores": [s.model_dump() for s in scores],
            "selected_vendor_id": selected,
            "status": "vendors_scored",
        },
    )
    return GenericStepResponse(
        request_id=request_id,
        status="vendors_scored",
        message=f"Scored {len(scores)} vendors",
        data={"vendor_scores": [s.model_dump() for s in scores], "selected_vendor_id": selected},
    )
