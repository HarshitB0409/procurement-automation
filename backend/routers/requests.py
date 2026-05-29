from typing import Optional

from fastapi import APIRouter, HTTPException

from models import ProcurementRequest
from services.request_store import get_request, list_requests

router = APIRouter(tags=["requests"])


@router.get("/requests", response_model=list[ProcurementRequest])
def get_requests(
    status: Optional[str] = None,
    approval_tier: Optional[str] = None,
    approver_role: Optional[str] = None,
) -> list[ProcurementRequest]:
    tier = approval_tier
    if approver_role == "manager" and not tier:
        tier = "needs_manager"
    elif approver_role == "finance" and not tier:
        tier = "needs_finance"

    stat = status
    if approver_role == "manager" and not stat:
        stat = "pending_manager"
    elif approver_role == "finance" and not stat:
        stat = "pending_finance"

    return list_requests(status=stat, approval_tier=tier)


@router.get("/requests/{request_id}", response_model=ProcurementRequest)
def get_request_by_id(request_id: str) -> ProcurementRequest:
    req = get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req
