# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/domain/audit_event.py
#
# PROPÓSITO:
# - Entidad de solo lectura de un evento de auditoría HTTP y los filtros
#   para listarlos (página Auditoría, solo admin).
#
# NOTAS:
# - Las filas las escribe AuditMiddleware en las tablas por año
#   `http_audit_<año>` (app/common/audit): cambios y errores, no las
#   consultas exitosas. La tabla `audit_logs` es otra cosa: el historial de
#   los agentes (bots/domain/bot_history.py), y no se lee aquí.
# - La entidad lleva solo lo útil para auditar: nunca los payloads
#   completos (pueden traer datos personales o respuestas enteras), solo el
#   `msg` de la respuesta y, en los eventos de login, el correo con el que
#   se intentó entrar (la persona aún no tiene sesión).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# event_type que resuelve AuditMiddleware._resolve_event_type.
AUDIT_EVENT_TYPES: tuple[str, ...] = (
    "LOGIN_OTP_REQUEST",
    "VERIFY_OTP",
    "LOGOUT",
    "GET_PROFILE",
    "ROTATE_TOKEN",
    "HTTP_REQUEST",
)

# Eventos sin sesión en los que el correo del body identifica a la persona.
AUDIT_LOGIN_EVENT_TYPES: frozenset[str] = frozenset({"LOGIN_OTP_REQUEST", "VERIFY_OTP"})

# Tipo de acción: consultas (no cambian nada) o cambios.
AUDIT_READ_METHODS: tuple[str, ...] = ("GET", "HEAD", "OPTIONS")
AUDIT_KINDS: tuple[str, ...] = ("read", "write")


@dataclass(frozen=True)
class AuditEvent:
    """Una petición HTTP auditada. `year` + `id` la identifican (tablas por año)."""
    year: int
    id: int
    ts: datetime
    user_id: int | None
    event_type: str
    method: str
    path: str
    status_code: int
    duration_ms: int | None
    ip: str | None
    user_agent: str | None
    response_msg: str | None
    login_email: str | None


@dataclass(frozen=True)
class AuditEventFilters:
    """Filtros ya validados. Fechas en UTC aware; `date_to` es exclusiva."""
    date_from: datetime | None = None
    date_to: datetime | None = None
    user_id: int | None = None
    event_type: str | None = None
    path_contains: str | None = None
    kind: str | None = None
    only_errors: bool = False
