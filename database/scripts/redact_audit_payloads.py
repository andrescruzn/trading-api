# -*- coding: utf-8 -*-

# ======================================================================
# database/scripts/redact_audit_payloads.py
#
# PROPÓSITO:
# - Re-aplicar el sanitizador actual a las filas YA guardadas en las
#   tablas `http_audit_{año}`. Hasta 2026-10 el sanitizador no redactaba
#   api_key / api_secret ni URLs de webhook, así que esas filas pueden
#   tener credenciales de exchange en claro.
#
# USO:
#   uv run python -m database.scripts.redact_audit_payloads --dry-run   # solo cuenta
#   uv run python -m database.scripts.redact_audit_payloads             # aplica
#
# NOTAS:
# - Idempotente: una fila ya redactada no cambia.
# - Procesa por lotes de 500 y confirma cada lote.
# - Después de correrlo, ROTAR las API keys que pudieron quedar expuestas.
# ======================================================================

from __future__ import annotations

import json
import sys

from sqlalchemy import text

from app.common.audit.audit_sanitizer import redact_request_data, redact_response_data
from app.extensions.db import SessionLocal

_BATCH = 500


def _load(raw: object) -> object:
    if raw is None or isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return raw


def _redact_table(session, table: str, dry_run: bool) -> int:
    changed = 0
    last_id = 0
    while True:
        rows = session.execute(
            text(
                f"SELECT id, request_payload, response_payload FROM `{table}` "
                "WHERE id > :last_id ORDER BY id LIMIT :batch"
            ),
            {"last_id": last_id, "batch": _BATCH},
        ).all()
        if not rows:
            break

        for row_id, req_raw, resp_raw in rows:
            last_id = row_id
            req, resp = _load(req_raw), _load(resp_raw)
            new_req, new_resp = redact_request_data(req), redact_response_data(resp)
            if new_req == req and new_resp == resp:
                continue
            changed += 1
            if not dry_run:
                session.execute(
                    text(
                        f"UPDATE `{table}` SET request_payload = :req, "
                        "response_payload = :resp WHERE id = :id"
                    ),
                    {
                        "req": json.dumps(new_req) if new_req is not None else None,
                        "resp": json.dumps(new_resp) if new_resp is not None else None,
                        "id": row_id,
                    },
                )
        if not dry_run:
            session.commit()
    return changed


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    session = SessionLocal()
    try:
        tables = [
            name
            for (name,) in session.execute(text("SHOW TABLES LIKE 'http\\_audit\\_%'")).all()
        ]
        total = 0
        for table in tables:
            changed = _redact_table(session, table, dry_run)
            total += changed
            print(f"{table}: {changed} filas {'por redactar' if dry_run else 'redactadas'}")
        print(f"Total: {total}{' (dry-run, sin cambios)' if dry_run else ''}")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
