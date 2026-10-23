# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/jwt/read_only_policy.py
#
# PROPÓSITO:
# - Regla del rol Socio (partner): ve todo lo que ve un super admin pero no
#   cambia nada. Toda escritura (POST/PUT/PATCH/DELETE) de un socio se
#   rechaza en el guard JWT, salvo las acciones sobre sí mismo.
#
# DECISIÓN:
# - Se aplica en `token_required_actual` (que ya lee el rol de la BD en
#   cada request) y no en un middleware: cubre todas las rutas con sesión
#   sin otra consulta a la BD. Es defensa en profundidad: las rutas de
#   escritura además exigen `super_admin_required`.
# - La lista permitida va por ruta (sin el prefijo /api) y es explícita:
#   lo que no esté aquí, un socio no lo puede escribir.
# ======================================================================

from __future__ import annotations

import re

from app.common.config import settings

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Escrituras que un socio sí puede hacer: su sesión, su perfil, su
# Telegram, la campana, simular estrategias y seguir señales compartidas.
_PARTNER_WRITE_ALLOWLIST: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"^/users/logout$",
        r"^/users/token/rotate$",
        r"^/users/me$",
        r"^/users/me/telegram(/.*)?$",
        r"^/notifications/seen$",
        r"^/backtests$",
        r"^/bots/\d+/subscription$",
    )
)


def _api_path(path: str) -> str:
    """Ruta sin el prefijo global de la API (`/api/bots` → `/bots`)."""
    prefix = settings.API_PREFIX.rstrip("/")
    if prefix and path.startswith(prefix):
        path = path[len(prefix):]
    return path.rstrip("/") or "/"


def is_read_only_violation(role_id: int, method: str, path: str) -> bool:
    """True si un socio intenta una escritura que no está en la lista permitida."""
    if int(role_id) != int(settings.AUTH_PARTNER_ROLE_ID):
        return False
    if method.upper() not in _UNSAFE_METHODS:
        return False
    api_path = _api_path(path)
    return not any(pattern.match(api_path) for pattern in _PARTNER_WRITE_ALLOWLIST)
