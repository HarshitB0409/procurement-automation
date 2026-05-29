from models import GenericStepResponse, VendorScore
from services.approval_rules import get_approval_tier, status_after_routing
from services.llm import generate_justification
from services.request_store import get_request, update_request


def generate_justification_for_request(request_id: str) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        return GenericStepResponse(
            request_id=request_id,
            status="submitted",
            message="Request not found",
        )

    raw_scores = req.vendor_scores or []
    scores = [VendorScore(**s) if isinstance(s, dict) else s for s in raw_scores]

    justification = generate_justification(
        req.item, req.quantity, req.cost, req.department, scores
    )
    tier = get_approval_tier(req.cost)
    status = status_after_routing(tier)

    update_request(
        request_id,
        {
            "justification": justification,
            "approval_tier": tier,
            "status": status,
        },
    )
    return GenericStepResponse(
        request_id=request_id,
        status=status,
        message="Justification generated",
        data={"justification": justification, "approval_tier": tier},
    )
