from fastapi import HTTPException

from models import SubmitRequestResponse
from services.approval_rules import get_approval_tier, requires_human_approval
from services.budget import check_budget, deduct_budget
from services.extraction_service import extract_vendors_for_request
from services.justification_service import generate_justification_for_request
import po
from po import ensure_winning_vendor_on_request, generate_po_for_request, three_way_match_for_request
from services.request_store import create_request, get_request, update_request
from services.scoring_service import score_vendors_for_request


def run_pipeline(
    item: str,
    quantity: int,
    estimated_cost: float,
    urgency: str,
    department: str,
    requester_id: str,
) -> SubmitRequestResponse:
    request_id = create_request(
        {
            "item": item,
            "quantity": quantity,
            "estimated_cost": estimated_cost,
            "urgency": urgency,
            "department": department,
            "requester_id": requester_id,
            "status": "submitted",
        }
    )

    # Read-only budget check — no deduction here
    budget = check_budget(department, estimated_cost)
    update_request(
        request_id,
        {"budget_check": budget.model_dump(), "status": "submitted"},
    )

    if not budget.passed:
        update_request(request_id, {"status": "budget_failed"})
        raise HTTPException(status_code=400, detail=budget.message)

    extract_vendors_for_request(request_id, use_mock_files=True)
    score_vendors_for_request(request_id)
    justify_result = generate_justification_for_request(request_id)

    tier = get_approval_tier(estimated_cost)

    if not requires_human_approval(tier):
        # Auto-approve: deduct budget here since no human step
        deduct_budget(department, estimated_cost)
        update_request(request_id, {"status": "auto_approved"})
        ensure_winning_vendor_on_request(request_id)
        generate_po_for_request(request_id)
        three_way_match_for_request(request_id)
        req = get_request(request_id)
        return SubmitRequestResponse(
            request_id=request_id,
            status=req.status if req else "po_generated",
            approval_tier=tier,
            message="Auto-approved: pipeline completed through PO generation and three-way match",
            request=req,
        )

    # Needs approval: do NOT deduct — wait for human
    if justify_result.status not in ("pending_manager", "pending_finance"):
        raise HTTPException(
            status_code=500,
            detail=f"Expected pending approval status, got '{justify_result.status}'",
        )

    req = get_request(request_id)
    return SubmitRequestResponse(
        request_id=request_id,
        status=justify_result.status,
        approval_tier=tier,
        message="Pipeline complete; awaiting human approval",
        request=req,
    )