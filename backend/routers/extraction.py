from fastapi import APIRouter

from models import ExtractVendorsBody, GenericStepResponse
from services.extraction_service import extract_vendors_for_request

router = APIRouter(tags=["extraction"])


@router.post("/extract-vendors", response_model=GenericStepResponse)
def extract_vendors(body: ExtractVendorsBody) -> GenericStepResponse:
    return extract_vendors_for_request(body.request_id, use_mock_files=body.use_mock_files)
