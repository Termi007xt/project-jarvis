"""The secret store (ADR-0030, PRD 18.3, NFR-022, FR-169, AT-016).

The assertions that matter here are byte-level: after a round trip, the
plaintext must not appear in the configuration file, the database, or the audit
log. Asserting "we called the encryption function" would prove nothing.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from jarvis.core.secrets import SecretStore, SecretStoreUnavailable
from jarvis.core.secrets import dpapi

WINDOWS_ONLY = pytest.mark.skipif(os.name != "nt", reason="DPAPI is a Windows facility")

SECRET_VALUE = "sk-live-Zx9QeRt7UvWpLmKj4HgFdSa2"


@pytest.fixture
def store(database, audit) -> SecretStore:
    return SecretStore(database, audit)


# -- the platform boundary --------------------------------------------------
def test_availability_matches_the_platform(store: SecretStore) -> None:
    assert store.available is (os.name == "nt")


@pytest.mark.skipif(os.name == "nt", reason="covers the non-Windows path")
def test_without_dpapi_nothing_is_stored_at_all(store: SecretStore) -> None:
    """Degrading to weaker protection would be worse than refusing (ADR-0010)."""
    assert store.unavailable_reason()
    with pytest.raises(SecretStoreUnavailable):
        store.set("search_api_key", SECRET_VALUE)
    assert store.list_names() == ()


# -- the API surface (asserted everywhere, so CI on Linux still checks it) --
def test_there_is_no_method_that_returns_every_plaintext() -> None:
    """ADR-0030: no API shape can dump every secret at once."""
    returns_plaintext = {"get"}
    for name in dir(SecretStore):
        if name.startswith("_"):
            continue
        assert name in returns_plaintext or "value" not in name, (
            f"SecretStore.{name} looks like it exposes secret values in bulk"
        )
    assert not hasattr(SecretStore, "all_values")
    assert not hasattr(SecretStore, "export")


def test_the_configuration_schema_still_refuses_a_secret_field(config_store) -> None:
    """The ADR-0006 route stays closed: no secret smuggled through user.yaml."""
    from jarvis.config.store import ConfigError

    with pytest.raises(ConfigError, match="not permitted"):
        config_store.set("secrets.search_api_key", SECRET_VALUE)


# -- round trip and non-leakage --------------------------------------------
@WINDOWS_ONLY
def test_a_secret_round_trips(store: SecretStore) -> None:
    store.set("search_api_key", SECRET_VALUE, purpose="search provider", owner="search")
    assert store.get("search_api_key") == SECRET_VALUE


@WINDOWS_ONLY
def test_the_plaintext_never_reaches_the_database_file(
    store: SecretStore, database, vault
) -> None:
    store.set("search_api_key", SECRET_VALUE)
    database.checkpoint()
    raw = Path(vault.db_path).read_bytes()
    assert SECRET_VALUE.encode("utf-8") not in raw
    assert SECRET_VALUE.encode("utf-16-le") not in raw


@WINDOWS_ONLY
def test_the_plaintext_never_reaches_the_audit_log(store: SecretStore, vault) -> None:
    store.set("search_api_key", SECRET_VALUE)
    store.get("search_api_key")
    text = Path(vault.audit_log_path).read_text(encoding="utf-8")
    assert SECRET_VALUE not in text
    # The event is still recorded — redaction is not silence.
    assert "search_api_key" in text


@WINDOWS_ONLY
def test_the_plaintext_never_reaches_the_configuration_file(
    store: SecretStore, config_store, vault
) -> None:
    store.set("search_api_key", SECRET_VALUE)
    config_store.set("logging.level", "DEBUG")
    user_config = Path(config_store.user_config_path)
    if user_config.exists():
        assert SECRET_VALUE not in user_config.read_text(encoding="utf-8")


@WINDOWS_ONLY
def test_metadata_is_readable_without_decrypting_anything(store: SecretStore) -> None:
    store.set("search_api_key", SECRET_VALUE, purpose="search provider", owner="search")
    described = store.describe()
    assert len(described) == 1
    assert described[0].name == "search_api_key"
    assert described[0].purpose == "search provider"
    assert described[0].protection == "dpapi_user"
    assert SECRET_VALUE not in repr(described)


@WINDOWS_ONLY
def test_a_tampered_ciphertext_fails_closed(store: SecretStore, database) -> None:
    """Never partial, never best-effort plaintext."""
    store.set("search_api_key", SECRET_VALUE)
    with database.transaction() as connection:
        connection.execute(
            "UPDATE secret SET ciphertext = ? WHERE name = ?",
            (b"\x00" * 64, "search_api_key"),
        )
    with pytest.raises(dpapi.DpapiError):
        store.get("search_api_key")


@WINDOWS_ONLY
def test_ciphertext_is_bound_to_the_secrets_name(store: SecretStore, database) -> None:
    """Lifting a value under a different name must not decrypt it."""
    store.set("search_api_key", SECRET_VALUE)
    row = database.query_one("SELECT ciphertext FROM secret WHERE name = ?", ("search_api_key",))
    with pytest.raises(dpapi.DpapiError):
        dpapi.unprotect(bytes(row["ciphertext"]), entropy=b"project-jarvis:secret:other_key")


@WINDOWS_ONLY
def test_replacing_a_secret_keeps_its_creation_time(store: SecretStore) -> None:
    first = store.set("search_api_key", SECRET_VALUE)
    second = store.set("search_api_key", "sk-live-different-value")
    assert second.created_at == first.created_at
    assert store.get("search_api_key") == "sk-live-different-value"


@WINDOWS_ONLY
def test_a_deleted_secret_is_gone(store: SecretStore) -> None:
    store.set("search_api_key", SECRET_VALUE)
    assert store.delete("search_api_key") is True
    assert store.get("search_api_key") is None
    assert store.delete("search_api_key") is False


@WINDOWS_ONLY
def test_an_empty_secret_is_refused(store: SecretStore) -> None:
    with pytest.raises(ValueError):
        store.set("search_api_key", "")


@WINDOWS_ONLY
def test_reading_records_when_it_was_last_used(store: SecretStore) -> None:
    store.set("search_api_key", SECRET_VALUE)
    assert store.describe()[0].last_used_at is None
    store.get("search_api_key")
    assert store.describe()[0].last_used_at is not None
