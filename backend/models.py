from datetime import datetime
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field

UserRole = Literal["requester", "manager", "finance"]
ApprovalTier = Literal["auto_approved", "needs_manager", "needs_finance"]
RequestStatus = Literal[
    "submitted",
    "budget_failed",
    "vendors_extracted",
    "vendors_scored",
    "justification_done",
    "auto_approved",
    "pending_manager",
    "pending_finance",
    "approved",
    "rejected",
    "po_generated",
    "matched",
]


class SubmitRequestBody(BaseModel):
    item: str
    quantity: int = Field(gt=0)
    estimated_cost: float = Field(gt=0)
    urgency: Literal["low", "medium", "high"]
    department: str
    requester_id: str = "user_requester_1"


class RequestIdBody(BaseModel):
    request_id: str


class ExtractVendorsBody(RequestIdBody):
    use_mock_files: bool = True


class ScoreVendorsBody(RequestIdBody):
    pass


class ApproveBody(BaseModel):
    request_id: str
    approver_id: str


class RejectBody(BaseModel):
    request_id: str
    approver_id: str
    reason: Optional[str] = None


class GeneratePOBody(RequestIdBody):
    pass


class ThreeWayMatchBody(BaseModel):
    request_id: str
    invoice_amount: Optional[float] = None
    receipt_qty: Optional[int] = None


class BudgetCheck(BaseModel):
    passed: bool
    remaining_before: float
    remaining_after: float
    message: str = ""


class ExtractedQuote(BaseModel):
    vendor_name: str
    item: str = ""
    unit_price: float = 0
    total_price: float = 0
    delivery_days: int = 0
    source_file: str = ""


class VendorScore(BaseModel):
    vendor_name: str
    price: float
    delivery_days: int
    sla_rating: float
    price_score: float
    speed_score: float
    rating_score: float
    total_score: float
    compliance_verified: bool = False


class POLineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float


class PurchaseOrder(BaseModel):
    number: str
    vendor_name: str
    line_items: list[POLineItem]
    total: float
    generated_at: str


class ThreeWayMatchResult(BaseModel):
    po_amount: float
    invoice_amount: float
    receipt_qty: int
    ordered_qty: int
    matched: bool
    notes: str


class ProcurementRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    item: str
    quantity: int
    estimated_cost: float = Field(validation_alias=AliasChoices("estimated_cost", "cost"))
    urgency: str
    department: str
    status: RequestStatus
    approval_tier: Optional[ApprovalTier] = None
    requester_id: str
    budget_check: Optional[BudgetCheck] = None
    extracted_quotes: list[ExtractedQuote] = []
    vendor_scores: list[VendorScore] = []
    justification: Optional[str] = None
    selected_vendor_id: Optional[str] = None
    po: Optional[PurchaseOrder] = None
    three_way_match: Optional[ThreeWayMatchResult] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost(self) -> float:
        """Backward compatibility for services that still read .cost."""
        return self.estimated_cost


class SubmitRequestResponse(BaseModel):
    request_id: str
    status: RequestStatus
    approval_tier: Optional[ApprovalTier] = None
    message: str
    request: Optional[ProcurementRequest] = None


class GenericStepResponse(BaseModel):
    request_id: str
    status: RequestStatus
    message: str
    data: dict = {}


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
