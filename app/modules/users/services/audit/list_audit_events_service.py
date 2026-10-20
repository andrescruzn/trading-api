# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/audit/list_audit_events_service.py
#
# CASO DE USO:
# - Un admin revisa la auditoría HTTP (página Auditoría): quién hizo qué,
#   cuándo y con qué resultado, paginado en el servidor.
#
# REGLAS:
# - Filtros opcionales: persona, tipo de evento, rango de fechas, texto en
#   la ruta, tipo de acción (consulta / cambio) y solo errores.
# - Fechas sin zona se toman como UTC; `date_to` es exclusiva y debe ser
#   posterior a `date_from`.
# - Sin `date_from` se buscan el año de `date_to` (o el actual) y el
#   anterior: las tablas son por año y así enero no aparece vacío.
# - Página ≥ 1 y tamaño 1–100 (PageRequest.of).
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.common.contracts import Page, PageRequest, ServiceResult
from app.common.utils import utc_now
from app.modules.users.domain import (
    AUDIT_EVENT_TYPES,
    AUDIT_KINDS,
    AuditEvent,
    AuditEventFilters,
    AuditEventRepository,
)

# Largo máximo del texto a buscar en la ruta (la columna es VARCHAR(512)).
PATH_FILTER_MAX_LEN = 200


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


class ListAuditEventsService:
    """Lista eventos de auditoría con filtros y paginación en el servidor."""

    def __init__(self, *, repo: AuditEventRepository):
        self._repo = repo

    def list(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        user_id: int | None = None,
        event_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        path: str | None = None,
        kind: str | None = None,
        only_errors: bool = False,
        now: datetime | None = None,
    ) -> ServiceResult[Page[AuditEvent]]:
        event = (event_type or "").strip().upper() or None
        if event is not None and event not in AUDIT_EVENT_TYPES:
            return ServiceResult.fail(code="AUDIT_INVALID_EVENT_TYPE", http_status=422)

        kind_clean = (kind or "").strip().lower() or None
        if kind_clean is not None and kind_clean not in AUDIT_KINDS:
            return ServiceResult.fail(code="AUDIT_INVALID_KIND", http_status=422)

        start = _as_utc(date_from)
        end = _as_utc(date_to)
        if start is not None and end is not None and start >= end:
            return ServiceResult.fail(code="AUDIT_INVALID_DATE_RANGE", http_status=422)

        path_clean = (path or "").strip() or None
        if path_clean is not None and len(path_clean) > PATH_FILTER_MAX_LEN:
            return ServiceResult.fail(code="AUDIT_INVALID_PATH", http_status=422)

        request = PageRequest.of(page, page_size)

        # Años a consultar (una tabla por año). `end` es exclusiva: el último
        # instante incluido es end - 1 µs.
        last_year = (end - timedelta(microseconds=1)).year if end else (now or utc_now()).year
        first_year = start.year if start else last_year - 1
        if first_year > last_year:
            return ServiceResult.ok(Page.empty(request))
        years = list(range(first_year, last_year + 1))

        filters = AuditEventFilters(
            date_from=start,
            date_to=end,
            user_id=int(user_id) if user_id is not None else None,
            event_type=event,
            path_contains=path_clean,
            kind=kind_clean,
            only_errors=bool(only_errors),
        )
        return ServiceResult.ok(self._repo.list_events(filters, years, request))
