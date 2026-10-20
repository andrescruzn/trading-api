# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/infrastructure/audit_event_repository_impl.py
#
# PROPÓSITO:
# - Leer la auditoría HTTP de las tablas por año `http_audit_<año>` con
#   SQLAlchemy Core (el nombre de la tabla es dinámico, no hay modelo ORM).
#
# DISEÑO:
# - Un SELECT por año con los mismos filtros; si el rango abarca varios
#   años se unen con UNION ALL y se ordena/pagina sobre el conjunto.
# - Nunca se leen los payloads completos: solo `$.msg` de la respuesta y,
#   en los eventos de login, `$.email` del request (JSON_EXTRACT en MySQL).
# - Índices existentes por tabla: (ts), (user_id, ts), (event_type, ts).
#   El filtro por texto en la ruta (LIKE '%x%') y por tipo de acción no usan
#   índice: recorren las filas del rango de fechas.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Table, and_, case, func, literal, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.common.audit.audit_table_factory import get_existing_table
from app.common.contracts import Page, PageRequest
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.users.domain.audit_event import (
    AUDIT_LOGIN_EVENT_TYPES,
    AUDIT_READ_METHODS,
    AuditEvent,
    AuditEventFilters,
)
from app.modules.users.domain.audit_event_repository import AuditEventRepository

# Longitud máxima de los textos extraídos del JSON (evita cargar respuestas raras).
_MAX_MSG_LEN = 500
_MAX_EMAIL_LEN = 255


def _escape_like(value: str) -> str:
    """Escapa los comodines de LIKE para buscar el texto tal cual."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _as_utc(dt: datetime) -> datetime:
    """MySQL devuelve TIMESTAMP sin zona; la conexión trabaja en UTC."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _json_text(value: str | None) -> str | None:
    """JSON_UNQUOTE de un null de JSON devuelve 'null': se trata como vacío."""
    return None if not value or value == "null" else value


def _to_db(dt: datetime) -> datetime:
    """UTC aware → naive UTC para comparar con la columna TIMESTAMP."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


class SqlAlchemyAuditEventRepository(SqlAlchemyRepository, AuditEventRepository):
    """Lectura paginada de `http_audit_<año>`."""

    def __init__(self, session: Session):
        super().__init__(session)

    # ------------------------------------------------------------------
    # Query por tabla
    # ------------------------------------------------------------------

    @staticmethod
    def _select_for(table: Table, year: int, filters: AuditEventFilters) -> Select:
        c = table.c
        response_msg = func.substr(
            func.json_unquote(func.json_extract(c.response_payload, "$.msg")), 1, _MAX_MSG_LEN
        )
        login_email = case(
            (
                c.event_type.in_(sorted(AUDIT_LOGIN_EVENT_TYPES)),
                func.substr(
                    func.json_unquote(func.json_extract(c.request_payload, "$.email")),
                    1,
                    _MAX_EMAIL_LEN,
                ),
            ),
            else_=None,
        )

        conditions = []
        if filters.date_from is not None:
            conditions.append(c.ts >= _to_db(filters.date_from))
        if filters.date_to is not None:
            conditions.append(c.ts < _to_db(filters.date_to))
        if filters.user_id is not None:
            conditions.append(c.user_id == filters.user_id)
        if filters.event_type:
            conditions.append(c.event_type == filters.event_type)
        if filters.path_contains:
            conditions.append(c.path.like(f"%{_escape_like(filters.path_contains)}%", escape="\\"))
        if filters.kind == "read":
            conditions.append(c.method.in_(AUDIT_READ_METHODS))
        elif filters.kind == "write":
            conditions.append(c.method.not_in(AUDIT_READ_METHODS))
        if filters.only_errors:
            conditions.append(c.status_code >= 400)

        stmt = select(
            literal(year).label("year"),
            c.id,
            c.ts,
            c.user_id,
            c.event_type,
            c.method,
            c.path,
            c.status_code,
            c.duration_ms,
            c.ip,
            c.user_agent,
            response_msg.label("response_msg"),
            login_email.label("login_email"),
        )
        return stmt.where(and_(*conditions)) if conditions else stmt

    # ------------------------------------------------------------------
    # Contrato
    # ------------------------------------------------------------------

    def list_events(
        self,
        filters: AuditEventFilters,
        years: list[int],
        page: PageRequest,
    ) -> Page[AuditEvent]:
        bind = self._session.connection()
        selects = [
            self._select_for(table, year, filters)
            for year in sorted(set(years), reverse=True)
            if (table := get_existing_table(year, bind)) is not None
        ]
        if not selects:
            return Page.empty(page)

        subquery = (union_all(*selects) if len(selects) > 1 else selects[0]).subquery("audit")

        total = int(
            self._session.execute(select(func.count()).select_from(subquery)).scalar() or 0
        )
        if total == 0 or page.offset >= total:
            return Page(items=[], total=total, page=page.page, page_size=page.page_size)

        rows = self._session.execute(
            select(subquery)
            .order_by(subquery.c.ts.desc(), subquery.c.id.desc())
            .offset(page.offset)
            .limit(page.limit)
        ).mappings()

        items = [
            AuditEvent(
                year=int(row["year"]),
                id=int(row["id"]),
                ts=_as_utc(row["ts"]),
                user_id=int(row["user_id"]) if row["user_id"] is not None else None,
                event_type=str(row["event_type"]),
                method=str(row["method"]),
                path=str(row["path"]),
                status_code=int(row["status_code"]),
                duration_ms=int(row["duration_ms"]) if row["duration_ms"] is not None else None,
                ip=row["ip"],
                user_agent=row["user_agent"],
                response_msg=_json_text(row["response_msg"]),
                login_email=_json_text(row["login_email"]),
            )
            for row in rows
        ]
        return Page(items=items, total=total, page=page.page, page_size=page.page_size)
