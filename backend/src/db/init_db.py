"""CLI helper to initialize the database schema."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..config.base_settings import settings
from .client import DatabaseClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize AETHERA database schema.")
    parser.add_argument("--dsn", help="Postgres DSN. Overrides POSTGRES_DSN environment variable.")
    parser.add_argument(
        "--schema",
        default=Path(__file__).with_name("schema.sql"),
        type=Path,
        help="Path to schema SQL file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dsn = args.dsn or settings.postgres_dsn
    client = DatabaseClient(dsn)

    with open(args.schema, encoding="utf-8") as f:
        schema_sql = f.read()

    with client.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)

    print("Database schema initialized.")


if __name__ == "__main__":
    main()

