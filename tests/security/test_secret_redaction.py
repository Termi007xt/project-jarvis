"""Secrets must never reach the audit log (PRD section 11.5, FR-259)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from jarvis.core.audit.models import AuditCategory
from jarvis.core.audit.redaction import REDACTED, classify_content, is_secret_key, redact
from jarvis.core.permissions.models import Decision, GrantScope, RiskLevel
from jarvis.core.tools.contract import ToolExecution, ToolSpec, Verification
from jarvis.core.tools.invoker import ToolCall

SECRET_VALUE = "hunter2-super-secret-value"


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "passwd",
        "api_key",
        "apiKey",
        "access_token",
        "refresh_token",
        "secret",
        "client_secret",
        "authorization",
        "cookie",
        "private_key",
        "passphrase",
        "totp",
        "recovery_phrase",
        "cvv",
        "card_number",
    ],
)
def test_secret_field_names_are_redacted(key: str) -> None:
    assert is_secret_key(key), f"'{key}' should be treated as a secret field"
    assert redact({key: SECRET_VALUE})[key] == REDACTED


@pytest.mark.parametrize(
    "value",
    [
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----",
        "Bearer abcdefghijklmnopqrstuvwxyz0123456789",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N",
        "AKIAIOSFODNN7EXAMPLE",
        "sk-abcdefghijklmnopqrstuvwxyz012345",
        "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        "postgres://user:hunter2@localhost:5432/db",
        "a" * 64 if False else "deadbeef" * 8,
    ],
)
def test_secret_looking_values_are_redacted_whatever_the_field_name(value: str) -> None:
    """Value-shape detection catches secrets in innocuously named fields."""
    redacted = redact({"harmless_note": value})["harmless_note"]
    assert REDACTED in redacted or redacted != value


def test_clipboard_content_is_described_not_stored(tmp_path) -> None:
    """PRD FR-259: log the action, never the plaintext content."""
    result = redact({"clipboard_content": "my bank password is hunter2"})
    entry = result["clipboard_content"]
    assert entry["redacted"] is True
    assert "hunter2" not in str(entry)
    assert entry["length"] == len("my bank password is hunter2")


def test_transcripts_and_document_text_are_not_stored_verbatim() -> None:
    for key in ("transcript", "document_text", "page_text", "ocr_text", "message_body"):
        entry = redact({key: "sensitive user content here"})[key]
        assert entry["redacted"] is True
        assert "sensitive user content" not in str(entry)


def test_nested_structures_are_redacted() -> None:
    payload = {
        "outer": {"inner": {"api_key": SECRET_VALUE, "safe": "keep me"}},
        "list": [{"password": SECRET_VALUE}, "plain"],
    }
    result = redact(payload)
    assert result["outer"]["inner"]["api_key"] == REDACTED
    assert result["outer"]["inner"]["safe"] == "keep me"
    assert result["list"][0]["password"] == REDACTED
    assert SECRET_VALUE not in str(result)


def test_oversized_values_are_truncated() -> None:
    """A log entry can never be used to smuggle out a document."""
    result = redact({"note": "x" * 5000}, max_chars=100)
    assert len(result["note"]) < 200
    assert "TRUNCATED" in result["note"]


def test_deeply_nested_and_huge_containers_are_bounded() -> None:
    deep = current = {}
    for _ in range(50):
        current["next"] = {}
        current = current["next"]
    assert "DEPTH_LIMIT" in str(redact(deep))

    wide = {"items": list(range(500))}
    assert "MORE ITEMS" in str(redact(wide))


def test_binary_values_are_described_not_embedded() -> None:
    entry = redact({"blob": b"\x00\x01\x02binary"})["blob"]
    assert entry["content_class"] == "binary"
    assert entry["length"] == 9


def test_classify_content_never_returns_the_content() -> None:
    for value in (SECRET_VALUE, "https://example.com", "+44 7700 900000", "line\nline"):
        assert value not in classify_content(value)


def test_audit_log_file_contains_no_secret_written_through_it(audit) -> None:
    audit.record(
        AuditCategory.TOOL,
        "test invocation",
        parameters={"api_key": SECRET_VALUE, "password": SECRET_VALUE, "safe": "visible"},
    )
    raw = audit.path.read_text(encoding="utf-8")
    assert SECRET_VALUE not in raw
    assert REDACTED in raw
    assert "visible" in raw


def test_secrets_passed_to_a_tool_do_not_reach_the_audit_log(
    registry, approving_invoker, permissions, audit
) -> None:
    """End to end: a tool call carrying a secret leaves no secret behind."""

    class _Params(BaseModel):
        api_key: str
        note: str

    class _Result(BaseModel):
        ok: bool = True

    class _EchoTool:
        spec = ToolSpec(
            tool_id="test.echo",
            version="1.0.0",
            description="test tool",
            input_model=_Params,
            output_model=_Result,
            risk=RiskLevel.LOW,
            required_capabilities=("system.read_health",),
            changes_state=False,
            verification="none",
            failure_codes=("failed",),
        )

        def run(self, context, parameters):
            return ToolExecution(output=_Result(), verification=Verification.NOT_APPLICABLE)

    registry.register(_EchoTool())
    permissions.grant(
        "system.read_health", Decision.ALLOW, GrantScope.ALWAYS, created_by="test"
    )

    result = approving_invoker.invoke(
        ToolCall(
            tool_id="test.echo",
            parameters={"api_key": SECRET_VALUE, "note": f"Bearer {SECRET_VALUE}0123456789"},
        )
    )
    assert result.succeeded

    raw = audit.path.read_text(encoding="utf-8")
    assert SECRET_VALUE not in raw, "a secret reached the audit log"
