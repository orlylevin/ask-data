#!/usr/bin/env python3
"""Execute a read-only DuckDB query and save the result as CSV."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import duckdb
import yaml

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|COPY|ATTACH|"
    r"DETACH|INSTALL|LOAD|EXPORT|IMPORT|CALL|MERGE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def load_database_path(config_path: Path) -> Path:
    if not config_path.exists():
        return Path("ask_data.duckdb")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    database = config.get("database", {})
    if database.get("engine") != "duckdb":
        raise ValueError("config/database.yaml must define engine: duckdb")
    return Path(database.get("path", "ask_data.duckdb"))


def validate_sql(sql: str) -> None:
    normalized = sql.strip().rstrip(";").strip()
    if not normalized:
        raise ValueError("SQL is empty")
    if FORBIDDEN.search(normalized):
        raise ValueError("Only read-only analytical SQL is allowed")
    if not re.match(r"^(SELECT|WITH)\b", normalized, re.IGNORECASE):
        raise ValueError("SQL must start with SELECT or WITH")


def read_sql(args: argparse.Namespace) -> str:
    if args.sql is not None:
        return args.sql
    if args.sql_file is not None:
        return args.sql_file.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide SQL with --sql, --sql-file, or standard input")


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--sql")
    source.add_argument("--sql-file", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--config", default=Path("config/database.yaml"), type=Path)
    args = parser.parse_args()

    try:
        sql = read_sql(args)
        validate_sql(sql)
        db_path = load_database_path(args.config)
        if not db_path.exists():
            raise FileNotFoundError(f"DuckDB database not found: {db_path}")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        connection = duckdb.connect(str(db_path), read_only=True)
        try:
            result = connection.execute(sql).fetchdf()
        finally:
            connection.close()

        result.to_csv(args.output, index=False)
        print(f"rows={len(result)}")
        print(f"columns={','.join(result.columns)}")
        print(f"output={args.output}")
        return 0
    except Exception as exc:
        print(f"error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
