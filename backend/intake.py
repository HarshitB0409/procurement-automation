from fastapi import APIRouter

from firebase import get_db
from models import SubmitRequestBody, SubmitRequestResponse
from pipeline import run_pipeline

router = APIRouter(tags=["intake"])


@router.post("/submit-request", response_model=SubmitRequestResponse)
def submit_request(body: SubmitRequestBody) -> SubmitRequestResponse:
    department = body.department.strip()
    db = get_db()

    print(f"[intake] Budget lookup: department={department!r}")
    all_budgets = [(doc.id, doc.to_dict()) for doc in db.collection("budgets").stream()]
    print(f"[intake] All budgets in DB ({len(all_budgets)}): {all_budgets}")

    matching = list(
        db.collection("budgets").where("department", "==", department).limit(1).stream()
    )
    print(
        f"[intake] Query: collection('budgets').where('department', '==', {department!r}) "
        f"-> {len(matching)} match(es)"
    )
    for doc in matching:
        print(f"[intake]   matched doc_id={doc.id!r}  data={doc.to_dict()!r}")

    return run_pipeline(
        item=body.item,
        quantity=body.quantity,
        estimated_cost=body.estimated_cost,
        urgency=body.urgency,
        department=department,
        requester_id=body.requester_id,
    )
