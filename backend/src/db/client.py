"""Lightweight database client."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg


class DatabaseClient:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection]:
        conn = psycopg.connect(self.dsn, autocommit=True)
        try:
            yield conn
        finally:
            conn.close()

