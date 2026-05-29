from typing import Any, Optional

from firebase import get_db
from models import ProcurementRequest, now_iso


def _doc_to_request(doc_id: str, data: dict) -> ProcurementRequest:
    payload = {k: v for k, v in data.items() if k != "id"}
    return ProcurementRequest.model_validate({**payload, "id": doc_id})


def get_request(request_id: str) -> Optional[ProcurementRequest]:
    db = get_db()
    doc = db.collection("requests").document(request_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    return _doc_to_request(doc.id, data)


def create_request(data: dict) -> str:
    db = get_db()
    data.setdefault("created_at", now_iso())
    data["updated_at"] = now_iso()
    _, ref = db.collection("requests").add(data)
    return ref.id


def update_request(request_id: str, fields: dict[str, Any]) -> Optional[ProcurementRequest]:
    db = get_db()
    ref = db.collection("requests").document(request_id)
    if not ref.get().exists:
        return None
    fields["updated_at"] = now_iso()
    ref.update(fields)
    doc = ref.get()
    return _doc_to_request(doc.id, doc.to_dict())


def list_requests(
    status: Optional[str] = None,
    approval_tier: Optional[str] = None,
) -> list[ProcurementRequest]:
    db = get_db()
    query = db.collection("requests")
    # One Firestore where-clause max (avoids composite-index requirement on real Firestore).
    if status:
        query = query.where("status", "==", status)
    elif approval_tier:
        query = query.where("approval_tier", "==", approval_tier)

    results = []
    for doc in query.stream():
        data = doc.to_dict() or {}
        if status and data.get("status") != status:
            continue
        if approval_tier and data.get("approval_tier") != approval_tier:
            continue
        results.append(_doc_to_request(doc.id, data))
    results.sort(key=lambda r: r.created_at or "", reverse=True)
    return results


def get_user_role(user_id: str) -> Optional[str]:
    db = get_db()
    doc = db.collection("users").document(user_id).get()
    if doc.exists:
        return (doc.to_dict() or {}).get("role")
    return None
