from fastapi import APIRouter

from models import GenericStepResponse, ScoreVendorsBody
from services.scoring_service import score_vendors_for_request

router = APIRouter(tags=["scoring"])


@router.post("/score-vendors", response_model=GenericStepResponse)
def score_vendors(body: ScoreVendorsBody) -> GenericStepResponse:
    return score_vendors_for_request(body.request_id)
