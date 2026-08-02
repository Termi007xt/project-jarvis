"""SQLite access (ADR-0002).

``jarvis.db`` is the canonical transactional store. WAL mode gives concurrent
readers alongside the scheduler's writer; foreign keys are on so that deleting
source material can cascade to derived records (PRD FR-167).

One connection per thread. sqlite3 connections are not safe to share across
threads, and the scheduler, workers and GUI all read.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

__all__ = ["Database", "DatabaseError"]


class DatabaseError(Exception):
    """The database could not be opened, migrated or queried."""


class Database:
    """A thread-safe handle to the vault database."""

    def __init__(self, path: Path, *, timeout_seconds: float = 10.0) -> None:
        self._path = path
        self._timeout = timeout_seconds
        self._local = threading.local()
        self._write_lock = threading.RLock()
        self._closed = False
        self._all_connections: list[sqlite3.Connection] = []
        self._connections_lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    # -- connections -------------------------------------------------------
    @property
    def connection(self) -> sqlite3.Connection:
        if self._closed:
            raise DatabaseError("database is closed")
        existing: sqlite3.Connection | None = getattr(self._local, "connection", None)
        if existing is not None:
            return existing

        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            connection = sqlite3.connect(
                self._path,
                timeout=self._timeout,
                isolation_level=None,  # explicit transaction control
                check_same_thread=True,
            )
        except sqlite3.Error as exc:  # pragma: no cover - filesystem failure
            raise DatabaseError(f"could not open {self._path}: {exc}") from exc

        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = %d" % int(self._timeout * 1000))
        self._local.connection = connection
        with self._connections_lock:
            self._all_connections.append(connection)
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """An exclusive write transaction. Nested use reuses the outer one."""
        connection = self.connection
        if connection.in_transaction:
            yield connection
            return
        with self._write_lock:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            connection.execute("COMMIT")

    # -- queries -----------------------------------------------------------
    def execute(self, sql: str, parameters: Sequence[Any] | dict[str, Any] = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, parameters)

    def query_all(
        self, sql: str, parameters: Sequence[Any] | dict[str, Any] = ()
    ) -> list[sqlite3.Row]:
        return list(self.connection.execute(sql, parameters).fetchall())

    def query_one(
        self, sql: str, parameters: Sequence[Any] | dict[str, Any] = ()
    ) -> sqlite3.Row | None:
        return self.connection.execute(sql, parameters).fetchone()

    def user_version(self) -> int:
        row = self.query_one("PRAGMA user_version")
        return int(row[0]) if row is not None else 0

    def set_user_version(self, version: int) -> None:
        # PRAGMA does not accept bound parameters; version is an int we control.
        self.connection.execute(f"PRAGMA user_version = {int(version)}")

    # -- lifecycle ---------------------------------------------------------
    def checkpoint(self) -> None:
        """Fold the WAL back into the main database file before shutdown."""
        try:
            self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.Error:  # pragma: no cover - best effort on shutdown
            pass

    def close(self) -> None:
        """Close every connection this database handed out."""
        self._closed = True
        with self._connections_lock:
            connections = list(self._all_connections)
            self._all_connections.clear()
        for connection in connections:
            try:
                connection.close()
            except sqlite3.Error:  # pragma: no cover
                pass
        if hasattr(self._local, "connection"):
            del self._local.connection

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
