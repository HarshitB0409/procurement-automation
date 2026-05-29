"""Seed Firestore with users, budgets, and vendors."""

from typing import Any


def seed(db: Any = None) -> None:
    if db is None:
        from firebase import get_db

        db = get_db()

    users = [
        {"id": "user_requester_1", "name": "Alice Requester", "role": "requester"},
        {"id": "user_manager_1", "name": "Bob Manager", "role": "manager"},
        {"id": "user_finance_1", "name": "Carol Finance", "role": "finance"},
    ]
    for u in users:
        db.collection("users").document(u["id"]).set(
            {"name": u["name"], "role": u["role"]}
        )

    budgets = [
        ("budget_it", {"department": "IT", "total": 100000, "remaining": 100000}),
        ("budget_hr", {"department": "HR", "total": 50000, "remaining": 50000}),
        ("budget_ops", {"department": "Operations", "total": 75000, "remaining": 75000}),
    ]
    print("[seed] Writing budgets collection:")
    for doc_id, b in budgets:
        db.collection("budgets").document(doc_id).set(b)
        print(f"  doc_id={doc_id!r}  data={b!r}")

    print("[seed] Verifying budgets after write:")
    for doc in db.collection("budgets").stream():
        print(f"  doc_id={doc.id!r}  data={doc.to_dict()!r}")

    vendors = [
        ("vendor_acme", {"name": "Acme Supplies Co.", "sla_rating": 4.0, "compliance_verified": True}),
        ("vendor_techdirect", {"name": "TechDirect Inc.", "sla_rating": 4.5, "compliance_verified": True}),
        ("vendor_global", {"name": "Global IT Partners", "sla_rating": 3.8, "compliance_verified": True}),
    ]
    for doc_id, v in vendors:
        db.collection("vendors").document(doc_id).set(v)

    budget_count = len(list(db.collection("budgets").stream()))
    print(f"[seed] Seed complete: {budget_count} budget(s) in collection 'budgets'")


if __name__ == "__main__":
    seed()
