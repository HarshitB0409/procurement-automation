from firebase import get_db
from models import BudgetCheck


def check_budget(department: str, cost: float) -> BudgetCheck:
    """Read-only check. Never deducts anything."""
    db = get_db()
    budgets = list(db.collection("budgets").where("department", "==", department).limit(1).stream())

    if not budgets:
        return BudgetCheck(
            passed=False,
            remaining_before=0,
            remaining_after=0,
            message=f"No budget found for department '{department}'",
        )

    budget_doc = budgets[0]
    budget_data = budget_doc.to_dict() or {}
    remaining = float(budget_data.get("remaining", 0))

    if remaining < cost:
        return BudgetCheck(
            passed=False,
            remaining_before=remaining,
            remaining_after=remaining,
            message=f"Insufficient budget: ${remaining:,.2f} remaining, need ${cost:,.2f}",
        )

    return BudgetCheck(
        passed=True,
        remaining_before=remaining,
        remaining_after=remaining - cost,
        message="Budget check passed",
    )


def deduct_budget(department: str, cost: float) -> None:
    """Actually deducts. Call only after confirmed approval or auto-approve."""
    db = get_db()
    budgets = list(db.collection("budgets").where("department", "==", department).limit(1).stream())

    if not budgets:
        return

    budget_doc = budgets[0]
    budget_data = budget_doc.to_dict() or {}
    remaining = float(budget_data.get("remaining", 0))
    db.collection("budgets").document(budget_doc.id).update({"remaining": remaining - cost})