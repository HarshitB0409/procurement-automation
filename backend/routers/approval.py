from fastapi import APIRouter

from models import ApproveBody, GenericStepResponse, RejectBody
from services.approval_service import approve_request, reject_request

router = APIRouter(tags=["approval"])


@router.post("/approve", response_model=GenericStepResponse)
def approve(body: ApproveBody) -> GenericStepResponse:
    return approve_request(body.request_id, body.approver_id)


@router.post("/reject", response_model=GenericStepResponse)
def reject(body: RejectBody) -> GenericStepResponse:
    return reject_request(body.request_id, body.approver_id, body.reason)
