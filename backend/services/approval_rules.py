from models import ApprovalTier


def get_approval_tier(cost: float) -> ApprovalTier:
    if cost < 5000:
        return "auto_approved"
    if cost < 20000:
        return "needs_manager"
    return "needs_finance"


def status_after_routing(approval_tier: ApprovalTier) -> str:
    if approval_tier == "auto_approved":
        return "auto_approved"
    if approval_tier == "needs_manager":
        return "pending_manager"
    return "pending_finance"


def requires_human_approval(approval_tier: ApprovalTier) -> bool:
    return approval_tier in ("needs_manager", "needs_finance")


def required_approver_role(approval_tier: ApprovalTier) -> str | None:
    if approval_tier == "needs_manager":
        return "manager"
    if approval_tier == "needs_finance":
        return "finance"
    return None
