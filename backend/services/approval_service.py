from fastapi import HTTPException

from models import GenericStepResponse
from services.approval_rules import required_approver_role
from services.budget import deduct_budget
from services.request_store import get_request, get_user_role, update_request


def approve_request(request_id: str, approver_id: str) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    role = get_user_role(approver_id)
    if not role:
        raise HTTPException(status_code=403, detail="Approver not found")

    tier = req.approval_tier
    required = required_approver_role(tier) if tier else None
    if required and role != required:
        raise HTTPException(
            status_code=403,
            detail=f"Approver role '{role}' cannot approve tier '{tier}' (requires {required})",
        )

    if req.status not in ("pending_manager", "pending_finance"):
        raise HTTPException(
            status_code=400,
            detail=f"Request status '{req.status}' is not pending approval",
        )

    # Deduct budget only on confirmed human approval
    deduct_budget(req.department, req.estimated_cost)

    update_request(
        request_id,
        {"status": "approved", "approver_id": approver_id},
    )
    return GenericStepResponse(
        request_id=request_id,
        status="approved",
        message="Request approved",
    )


def reject_request(request_id: str, approver_id: str, reason: str | None = None) -> GenericStepResponse:
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status not in ("pending_manager", "pending_finance"):
        raise HTTPException(
            status_code=400,
            detail=f"Request status '{req.status}' is not pending approval",
        )

    # No budget deduction on rejection
    update_request(
        request_id,
        {
            "status": "rejected",
            "rejection_reason": reason or "",
            "rejected_by": approver_id,
        },
    )
    return GenericStepResponse(
        request_id=request_id,
        status="rejected",
        message="Request rejected",
    )