"""Audit log durability and field coverage (PRD section 11.5)."""

from __future__ import annotations

import json

from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.types import AuditRecorded

#: PRD section 11.5 requires every consequential action to log these.
REQUIRED_FIELDS = {
    "occurred_at",
    "task_id",
    "conversation_id",
    "tool_id",
    "parameters",
    "permission_decision",
    "pre_state",
    "result",
    "verification",
    "error",
    "evidence_ref",
}


def test_a_record_carries_every_prd_required_field(audit: AuditLog) -> None:
    audit.record(
        AuditCategory.TOOL,
        "did a thing",
        task_id="t1",
        conversation_id="c1",
        tool_id="test.tool",
        permission_decision="allow",
        parameters={"a": 1},
        pre_state={"before": True},
        result="succeeded",
        verification="verified",
        error=None,
        evidence_ref="screenshot-1",
    )
    record = audit.read_all()[-1]
    assert REQUIRED_FIELDS <= set(record)


def test_the_jsonl_file_is_append_only_and_one_object_per_line(audit: AuditLog) -> None:
    for index in range(5):
        audit.record(AuditCategory.LIFECYCLE, f"event {index}")

    lines = audit.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    for line in lines:
        json.loads(line)  # each line parses independently


def test_records_survive_a_new_log_instance(vault, database, events) -> None:
    first = AuditLog(vault.audit_log_path, database=database, event_bus=events)
    first.record(AuditCategory.LIFECYCLE, "before restart")

    second = AuditLog(vault.audit_log_path, database=database, event_bus=events)
    second.record(AuditCategory.LIFECYCLE, "after restart")

    summaries = [record["summary"] for record in second.read_all()]
    assert summaries == ["before restart", "after restart"]


def test_records_are_indexed_in_sqlite_for_search(audit: AuditLog, database) -> None:
    audit.record(AuditCategory.PERMISSION, "asked", capability_id="fs.read_approved")
    rows = database.query_all("SELECT * FROM audit_event")
    assert len(rows) == 1
    assert rows[0]["capability_id"] == "fs.read_approved"


def test_query_filters_by_category_task_and_capability(audit: AuditLog) -> None:
    audit.record(AuditCategory.TASK, "task event", task_id="t1")
    audit.record(AuditCategory.PERMISSION, "permission event", capability_id="clipboard.read")
    audit.record(AuditCategory.TASK, "other task", task_id="t2")

    assert len(audit.query(category=AuditCategory.TASK)) == 2
    assert len(audit.query(task_id="t1")) == 1
    assert len(audit.query(capability_id="clipboard.read")) == 1


def test_query_falls_back_to_the_file_when_sqlite_is_off(vault, database, events) -> None:
    log = AuditLog(vault.audit_log_path, database=database, event_bus=events,
                   write_to_sqlite=False)
    log.record(AuditCategory.TASK, "file only", task_id="t1")
    assert len(log.query(task_id="t1")) == 1
    assert database.query_all("SELECT * FROM audit_event") == []


def test_recording_publishes_an_event(audit: AuditLog, events) -> None:
    received = []
    events.subscribe(AuditRecorded, received.append)
    audit.record(AuditCategory.LIFECYCLE, "something happened")
    assert len(received) == 1
    assert received[0].summary == "something happened"


def test_export_writes_a_copy(audit: AuditLog, tmp_path) -> None:
    audit.record(AuditCategory.LIFECYCLE, "exportable")
    destination = audit.export(tmp_path / "exported.jsonl")
    assert destination.is_file()
    assert "exportable" in destination.read_text(encoding="utf-8")


def test_an_sqlite_failure_does_not_lose_the_record(vault, database, events) -> None:
    """The JSONL file is the record of truth; the index is best effort."""
    log = AuditLog(vault.audit_log_path, database=database, event_bus=events)
    database.close()  # break the index sink

    log.record(AuditCategory.LIFECYCLE, "written despite index failure")
    assert any(
        record["summary"] == "written despite index failure" for record in log.read_all()
    )


def test_the_instance_id_is_recorded_for_crash_attribution(audit: AuditLog) -> None:
    audit.record(AuditCategory.LIFECYCLE, "started")
    assert audit.read_all()[-1]["instance_id"] == "test-instance"
