"""Secret redaction for the audit log (PRD section 11.5, FR-259).

Redaction happens *before* serialisation, not at display time. Anything written
to the audit log has already lost its secrets, so exporting or sharing the log
cannot leak them.

Two independent passes:

* by key   — the name of the field suggests a secret
* by value — the value itself looks like a secret regardless of its field name

Both are deliberately over-eager. A redacted audit entry is an inconvenience; a
leaked one is a security incident.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

__all__ = [
    "REDACTED",
    "TRUNCATION_SUFFIX",
    "redact",
    "redact_text",
    "is_secret_key",
    "classify_content",
]

REDACTED = "[REDACTED]"
TRUNCATION_SUFFIX = "…[TRUNCATED]"

#: Field names whose value is never written in plaintext.
_SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|pwd|passphrase|secret|token|api[_-]?key|apikey|access[_-]?key"
    r"|private[_-]?key|credential|auth|authorization|bearer|cookie|session[_-]?id"
    r"|otp|totp|mfa|2fa|pin|cvv|card[_-]?number|account[_-]?number|seed[_-]?phrase"
    r"|recovery[_-]?phrase|mnemonic|signature|salt|nonce)",
    re.IGNORECASE,
)

#: Field names that carry user content which must never be logged verbatim
#: (PRD FR-259 for clipboard; the same reasoning covers transcripts and
#: document text).
_CONTENT_KEY_PATTERN = re.compile(
    r"(clipboard|clipboard[_-]?content|transcript|document[_-]?text|page[_-]?text"
    r"|message[_-]?body|ocr[_-]?text|screen[_-]?text)",
    re.IGNORECASE,
)

_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("pem_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-~+/]{16,}=*", re.IGNORECASE)),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("aws_access_key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("private_key_body", re.compile(r"\b[A-Fa-f0-9]{64,}\b")),
    ("connection_string", re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s:/]+:[^\s@/]+@")),
)

_MAX_CONTAINER_ITEMS = 50
_MAX_DEPTH = 8


def is_secret_key(key: str) -> bool:
    return bool(_SECRET_KEY_PATTERN.search(key))


def is_content_key(key: str) -> bool:
    return bool(_CONTENT_KEY_PATTERN.search(key))


def classify_content(value: str) -> str:
    """Describe a value without reproducing it.

    Used where the *shape* of user content matters for debugging but the content
    itself must not be stored.
    """
    if not value:
        return "empty"
    for label, pattern in _VALUE_PATTERNS:
        if pattern.search(value):
            return f"redacted:{label}"
    if re.fullmatch(r"\s*https?://\S+\s*", value):
        return "url"
    if re.fullmatch(r"[\d\s+\-()]{7,}", value):
        return "numeric"
    if "\n" in value:
        return "multiline_text"
    return "text"


def redact_text(value: str, *, max_chars: int = 512) -> str:
    """Redact secret-looking substrings, then bound the length."""
    for _label, pattern in _VALUE_PATTERNS:
        value = pattern.sub(REDACTED, value)
    if len(value) > max_chars:
        value = value[:max_chars] + TRUNCATION_SUFFIX
    return value


def redact(value: Any, *, max_chars: int = 512, _depth: int = 0) -> Any:
    """Return a copy of ``value`` safe to persist in the audit log.

    Mappings, sequences and scalars are handled; anything else is coerced to a
    bounded string. Recursion and container sizes are capped so a hostile or
    accidental structure cannot make an audit write unbounded.
    """
    if _depth > _MAX_DEPTH:
        return "[DEPTH_LIMIT]"

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return redact_text(value, max_chars=max_chars)

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for index, (raw_key, raw_value) in enumerate(value.items()):
            if index >= _MAX_CONTAINER_ITEMS:
                result["…"] = f"[{len(value) - _MAX_CONTAINER_ITEMS} MORE KEYS]"
                break
            key = str(raw_key)
            if is_secret_key(key):
                result[key] = REDACTED
            elif is_content_key(key):
                text = raw_value if isinstance(raw_value, str) else str(raw_value)
                result[key] = {
                    "redacted": True,
                    "content_class": classify_content(text),
                    "length": len(text),
                }
            else:
                result[key] = redact(raw_value, max_chars=max_chars, _depth=_depth + 1)
        return result

    if isinstance(value, (list, tuple, set, frozenset)) or (
        isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
    ):
        items = list(value)
        truncated = items[:_MAX_CONTAINER_ITEMS]
        redacted_items = [
            redact(item, max_chars=max_chars, _depth=_depth + 1) for item in truncated
        ]
        if len(items) > _MAX_CONTAINER_ITEMS:
            redacted_items.append(f"[{len(items) - _MAX_CONTAINER_ITEMS} MORE ITEMS]")
        return redacted_items

    if isinstance(value, (bytes, bytearray)):
        return {"redacted": True, "content_class": "binary", "length": len(value)}

    return redact_text(str(value), max_chars=max_chars)
