"""End-to-end pipeline test using mock DB."""

import os

os.environ.setdefault("USE_MOCK_DB", "true")

from seed import seed
from pipeline import run_pipeline
from services.request_store import get_request
from services.approval_service import approve_request
from services.po_service import generate_po_for_request, three_way_match_for_request


def test_auto_approve_flow():
    seed()
    result = run_pipeline(
        item="USB Cables",
        quantity=50,
        cost=1200.0,
        urgency="low",
        department="IT",
        requester_id="user_requester_1",
    )
    assert result.status in ("po_generated", "auto_approved", "matched")
    assert result.approval_tier == "auto_approved"
    req = get_request(result.request_id)
    assert req is not None
    assert req.vendor_scores
    assert req.justification
    print(f"[PASS] Auto-approve flow: {result.request_id} -> {req.status}")


def test_manager_approval_flow():
    seed()
    result = run_pipeline(
        item="Office Chairs",
        quantity=20,
        cost=8000.0,
        urgency="medium",
        department="HR",
        requester_id="user_requester_1",
    )
    assert result.status == "pending_manager"
    approve_request(result.request_id, "user_manager_1")
    generate_po_for_request(result.request_id)
    match = three_way_match_for_request(result.request_id)
    req = get_request(result.request_id)
    assert match.data["three_way_match"]["matched"] is True
    print(f"[PASS] Manager flow: {result.request_id} -> {req.status}")


if __name__ == "__main__":
    test_auto_approve_flow()
    test_manager_approval_flow()
    print("\nAll E2E tests passed.")
