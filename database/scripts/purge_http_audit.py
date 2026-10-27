# -*- coding: utf-8 -*-

# ======================================================================
# database/scripts/purge_http_audit.py
#
# PROPÓSITO:
# - Borrar de las tablas `http_audit_{año}` las filas que ya no aportan:
#   las más viejas que la retención y, con --drop-reads, las consultas
#   exitosas (GET/HEAD/OPTIONS < 400) que se guardaban antes de 2026-10-27.
#
# USO:
#   uv run python -m database.scripts.purge_http_audit --dry-run                 # solo cuenta
#   uv run python -m database.scripts.purge_http_audit                           # > 180 días
#   uv run python -m database.scripts.purge_http_audit --older-than-days 90
#   uv run python -m database.scripts.purge_http_audit --drop-reads --dry-run    # limpieza única
#
# NOTAS:
# - Borra por lotes de 5.000 ids y confirma cada lote (no bloquea la tabla).
# - Una tabla de un año que queda vacía no se elimina: el middleware la
#   seguiría usando si es la del año en curso.
# - Lo ejecuta el usuario, no el agente.
# ======================================================================

from __future__ import annotations

import argparse
import sys
from datetime import timedelta

from sqlalchemy import text

from app.common.utils import utc_now
from app.extensions.db import SessionLocal

_BATCH = 5000
_DEFAULT_RETENTION_DAYS = 180

# Consultas exitosas: hoy el middleware ya no las guarda.
_READS_CONDITION = "(method IN ('GET', 'HEAD', 'OPTIONS') AND status_code < 400)"


def _where(drop_reads: bool) -> str:
    condition = "ts < :cutoff"
    if drop_reads:
        condition = f"({condition} OR {_READS_CONDITION})"
    return condition


def _purge_table(session, table: str, where: str, cutoff, dry_run: bool) -> int:
    params = {"cutoff": cutoff}
    if dry_run:
        return session.execute(
            text(f"SELECT COUNT(*) FROM `{table}` WHERE {where}"), params
        ).scalar_one()

    deleted = 0
    while True:
        result = session.execute(
            text(f"DELETE FROM `{table}` WHERE {where} ORDER BY id LIMIT {_BATCH}"),
            params,
        )
        session.commit()
        deleted += result.rowcount
        if result.rowcount < _BATCH:
            return deleted


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Purga las tablas http_audit_<año>.")
    parser.add_argument(
        "--older-than-days",
        type=int,
        default=_DEFAULT_RETENTION_DAYS,
        help=f"Borra las filas con más de N días (por defecto {_DEFAULT_RETENTION_DAYS}).",
    )
    parser.add_argument(
        "--drop-reads",
        action="store_true",
        help="Borra también las consultas exitosas (GET/HEAD/OPTIONS < 400).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo cuenta, no borra.")
    args = parser.parse_args(argv)

    if args.older_than_days < 1:
        print("--older-than-days debe ser 1 o más.")
        return 2

    # `ts` se guarda en UTC sin zona: el corte va igual
    cutoff = utc_now().replace(tzinfo=None) - timedelta(days=args.older_than_days)
    where = _where(args.drop_reads)

    session = SessionLocal()
    try:
        tables = [
            name
            for (name,) in session.execute(text("SHOW TABLES LIKE 'http\\_audit\\_%'")).all()
        ]
        total = 0
        for table in tables:
            count = _purge_table(session, table, where, cutoff, args.dry_run)
            total += count
            print(f"{table}: {count} filas {'por borrar' if args.dry_run else 'borradas'}")
        print(f"Total: {total}{' (dry-run, sin cambios)' if args.dry_run else ''}")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
