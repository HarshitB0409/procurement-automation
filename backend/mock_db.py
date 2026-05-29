"""In-memory Firestore substitute for local dev without Firebase credentials."""

from __future__ import annotations

import copy
import uuid
from typing import Any, Optional


class _DocSnapshot:
    def __init__(self, doc_id: str, data: dict | None, exists: bool):
        self.id = doc_id
        self._data = data
        self.exists = exists

    def to_dict(self) -> dict | None:
        return copy.deepcopy(self._data) if self._data is not None else None


class _DocRef:
    def __init__(self, store: "MockFirestore", collection: str, doc_id: str):
        self._store = store
        self._collection = collection
        self._id = doc_id

    @property
    def id(self) -> str:
        return self._id

    def get(self) -> _DocSnapshot:
        data = self._store._collections.get(self._collection, {}).get(self._id)
        return _DocSnapshot(self._id, data, data is not None)

    def set(self, data: dict) -> None:
        self._store._collections.setdefault(self._collection, {})[self._id] = copy.deepcopy(data)

    def update(self, fields: dict) -> None:
        coll = self._store._collections.setdefault(self._collection, {})
        if self._id not in coll:
            coll[self._id] = {}
        coll[self._id].update(copy.deepcopy(fields))


class _Query:
    def __init__(self, store: "MockFirestore", collection: str):
        self._store = store
        self._collection = collection
        self._filters: list[tuple[str, str, Any]] = []
        self._limit: int | None = None

    def where(self, field: str, op: str, value: Any) -> "_Query":
        if op == "==":
            self._filters.append((field, op, value))
        return self

    def limit(self, n: int) -> "_Query":
        self._limit = n
        return self

    def stream(self):
        coll = self._store._collections.get(self._collection, {})
        count = 0
        for doc_id, data in coll.items():
            if all(data.get(f) == v for f, _, v in self._filters):
                yield _DocSnapshot(doc_id, data, True)
                count += 1
                if self._limit is not None and count >= self._limit:
                    return

    def __iter__(self):
        return iter(list(self.stream()))


class _CollectionRef:
    def __init__(self, store: "MockFirestore", name: str):
        self._store = store
        self._name = name

    def document(self, doc_id: str) -> _DocRef:
        return _DocRef(self._store, self._name, doc_id)

    def add(self, data: dict) -> tuple[Any, _DocRef]:
        doc_id = uuid.uuid4().hex[:12]
        ref = self.document(doc_id)
        ref.set(data)
        return None, ref

    def where(self, field: str, op: str, value: Any) -> _Query:
        q = _Query(self._store, self._name)
        return q.where(field, op, value)

    def stream(self):
        coll = self._store._collections.get(self._name, {})
        for doc_id, data in coll.items():
            yield _DocSnapshot(doc_id, data, True)


class MockFirestore:
    def __init__(self):
        self._collections: dict[str, dict[str, dict]] = {}

    def collection(self, name: str) -> _CollectionRef:
        return _CollectionRef(self, name)

    def transaction(self):
        return _MockTransaction(self)


class _MockTransaction:
    def __init__(self, db: MockFirestore):
        self._db = db


def transactional(fn):
    def wrapper(transaction, *args, **kwargs):
        return fn(transaction, *args, **kwargs)

    return wrapper


_mock_instance: MockFirestore | None = None


def get_mock_db() -> MockFirestore:
    global _mock_instance
    if _mock_instance is None:
        _mock_instance = MockFirestore()
    return _mock_instance
