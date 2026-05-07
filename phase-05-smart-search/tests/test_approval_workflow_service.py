from __future__ import annotations

from copy import deepcopy

from backend.services.approval_workflow_service import ApprovalWorkflowService


class _Result:
    def __init__(self, data):
        self.data = data


class _TableQuery:
    def __init__(self, db: dict[str, list[dict]], table: str):
        self.db = db
        self.table = table
        self._filters: list[tuple[str, object]] = []
        self._insert: dict | None = None
        self._update: dict | None = None
        self._limit: int | None = None
        self._desc = False
        self._select_cols: list[str] | None = None

    def select(self, cols: str):
        self._select_cols = [c.strip() for c in cols.split(",")]
        return self

    def eq(self, field: str, value):
        self._filters.append((field, value))
        return self

    def order(self, _field: str, desc: bool = False):
        self._desc = desc
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def insert(self, payload: dict):
        self._insert = payload
        return self

    def update(self, payload: dict):
        self._update = payload
        return self

    def execute(self):
        rows = self.db.setdefault(self.table, [])
        if self._insert is not None:
            rows.append(deepcopy(self._insert))
            return _Result([self._insert])

        filtered = [r for r in rows if all(r.get(k) == v for k, v in self._filters)]
        if self._update is not None:
            for row in filtered:
                row.update(deepcopy(self._update))
            return _Result(filtered)

        if self._desc:
            filtered = list(reversed(filtered))
        if self._limit is not None:
            filtered = filtered[: self._limit]
        if self._select_cols:
            filtered = [{k: r.get(k) for k in self._select_cols} for r in filtered]
        return _Result(filtered)


class _FakeClient:
    def __init__(self):
        self.db: dict[str, list[dict]] = {"approvals": []}

    def table(self, name: str):
        return _TableQuery(self.db, name)


def test_duplicate_intent_is_idempotent():
    client = _FakeClient()
    svc = ApprovalWorkflowService(client)
    first = svc.process_action_intent("s1", "u1", "Demo", "Book a call about SIP", "chat")
    second = svc.process_action_intent("s1", "u1", "Demo", "Book a call about SIP", "chat")
    assert first["created"] is True
    assert second.get("duplicate") is True
    assert len(client.db["approvals"]) == 1


def test_cancel_marks_pending_as_rejected():
    client = _FakeClient()
    svc = ApprovalWorkflowService(client)
    svc.process_action_intent("s1", "u1", "Demo", "Book a call about SIP", "chat")
    cancel = svc.process_action_intent("s1", "u1", "Demo", "Actually cancel my booking", "chat")
    assert cancel.get("cancelled") is True
    assert client.db["approvals"][0]["status"] == "rejected"


def test_low_confidence_does_not_create():
    client = _FakeClient()
    svc = ApprovalWorkflowService(client)
    result = svc.process_action_intent("s1", "u1", "Demo", "maybe schedule something", "chat")
    assert result["created"] is False
    assert len(client.db["approvals"]) == 0
