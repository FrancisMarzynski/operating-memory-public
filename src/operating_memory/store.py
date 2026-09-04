"""SQLite implementation of the narrow memory repository API."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Protocol

from .model import Decision, Entity, JournalEntry


class MemoryRepository(Protocol):
    """Storage boundary shared by the importer and read-only CLI."""

    def upsert(self, record: Entity | Decision | JournalEntry) -> str: ...
    def list_kinds(self) -> list[str]: ...
    def get_entity(self, kind: str, key: str) -> Entity | None: ...
    def decisions_for(self, kind: str, key: str) -> list[Decision]: ...


class MemoryStore:
    """A local store containing only imported generic records."""

    def __init__(self, database: Path) -> None:
        self.database = database

    @contextmanager
    def _write_connection(self) -> Generator[sqlite3.Connection, None, None]:
        connection = sqlite3.connect(self.database)
        try:
            connection.row_factory = sqlite3.Row
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS entities (
                  identity TEXT PRIMARY KEY, kind TEXT NOT NULL, key TEXT NOT NULL,
                  title TEXT NOT NULL, source_path TEXT NOT NULL, body TEXT NOT NULL,
                  content_hash TEXT NOT NULL, UNIQUE(kind, key)
                );
                CREATE TABLE IF NOT EXISTS decisions (
                  identity TEXT PRIMARY KEY,
                  entity_identity TEXT NOT NULL REFERENCES entities(identity),
                  date TEXT NOT NULL,
                  body TEXT NOT NULL,
                  source_path TEXT NOT NULL,
                  content_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS journals (
                  identity TEXT PRIMARY KEY, date TEXT NOT NULL, source_path TEXT NOT NULL,
                  body TEXT NOT NULL, content_hash TEXT NOT NULL
                );
            """)
            yield connection
            connection.commit()
        finally:
            connection.close()

    @contextmanager
    def _read_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Open an existing database without creating it or its schema."""
        connection = sqlite3.connect(f"{self.database.resolve().as_uri()}?mode=ro", uri=True)
        try:
            connection.row_factory = sqlite3.Row
            yield connection
        finally:
            connection.close()

    def upsert(self, record: Entity | Decision | JournalEntry) -> str:
        table, values = self._values(record)
        with self._write_connection() as connection:
            current = connection.execute(
                f"SELECT content_hash FROM {table} WHERE identity = ?", (record.identity,)
            ).fetchone()
            if current is None:
                columns = ", ".join(values)
                marks = ", ".join("?" for _ in values)
                connection.execute(
                    f"INSERT INTO {table} ({columns}) VALUES ({marks})", tuple(values.values())
                )
                return "created"
            if current["content_hash"] == record.content_hash:
                return "unchanged"
            setters = ", ".join(f"{column} = ?" for column in values if column != "identity")
            connection.execute(
                f"UPDATE {table} SET {setters} WHERE identity = ?",
                (*[value for key, value in values.items() if key != "identity"], record.identity),
            )
            return "updated"

    @staticmethod
    def _values(record: Entity | Decision | JournalEntry) -> tuple[str, dict[str, str]]:
        if isinstance(record, Entity):
            return "entities", record.__dict__
        if isinstance(record, Decision):
            return "decisions", record.__dict__
        return "journals", record.__dict__

    def list_kinds(self) -> list[str]:
        with self._read_connection() as connection:
            return [
                row[0]
                for row in connection.execute("SELECT DISTINCT kind FROM entities ORDER BY kind")
            ]

    def get_entity(self, kind: str, key: str) -> Entity | None:
        with self._read_connection() as connection:
            row = connection.execute(
                "SELECT * FROM entities WHERE kind = ? AND key = ?", (kind, key)
            ).fetchone()
        return Entity(**dict(row)) if row else None

    def decisions_for(self, kind: str, key: str) -> list[Decision]:
        with self._read_connection() as connection:
            rows = connection.execute(
                """SELECT decisions.* FROM decisions
                JOIN entities ON decisions.entity_identity = entities.identity
                WHERE entities.kind = ? AND entities.key = ?
                ORDER BY decisions.date, decisions.identity""",
                (kind, key),
            ).fetchall()
        return [Decision(**dict(row)) for row in rows]
