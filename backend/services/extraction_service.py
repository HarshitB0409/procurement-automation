from services.pdf_parser import load_mock_quotes
from services.request_store import get_request, update_request
from models import ExtractedQuote, GenericStepResponse


def extract_vendors_for_request(request_id: str, use_mock_files: bool = True) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        return GenericStepResponse(
            request_id=request_id,
            status="submitted",
            message="Request not found",
        )

    quotes: list[ExtractedQuote] = []
    if use_mock_files:
        # Pass both request_id AND estimated cost so prices scale to the request
        quotes = load_mock_quotes(
            request_id=request_id,
            estimated_cost=req.estimated_cost,
            quantity=req.quantity,
        )

    update_request(
        request_id,
        {
            "extracted_quotes": [q.model_dump() for q in quotes],
            "status": "vendors_extracted",
        },
    )
    return GenericStepResponse(
        request_id=request_id,
        status="vendors_extracted",
        message=f"Extracted {len(quotes)} vendor quotes",
        data={"extracted_quotes": [q.model_dump() for q in quotes]},
    )