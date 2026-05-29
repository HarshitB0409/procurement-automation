import os
from functools import lru_cache
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from config import settings


def _use_mock() -> bool:
    if settings.use_mock_db:
        return True
    cred_path = settings.google_application_credentials or os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )
    return not (cred_path and os.path.isfile(cred_path))


def _ensure_mock_seeded(db: Any) -> None:
    """Seed mock DB when empty (seed.py in another process does not share memory)."""
    budgets = list(db.collection("budgets").stream())
    if budgets:
        print(f"[firebase] Mock DB already has {len(budgets)} budget(s)")
        return
    print("[firebase] Mock DB has no budgets — seeding now...")
    from seed import seed

    seed(db=db)
    budgets = list(db.collection("budgets").stream())
    print(f"[firebase] After seed: {len(budgets)} budget(s) in mock DB")


@lru_cache
def get_db() -> Any:
    if _use_mock():
        from mock_db import get_mock_db

        db = get_mock_db()
        _ensure_mock_seeded(db)
        return db

    if not firebase_admin._apps:
        cred_path = settings.google_application_credentials or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS", ""
        )
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(
            cred,
            {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None,
        )
    return firestore.client()
