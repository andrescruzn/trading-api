# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/jwt/auth_exceptions.py
#
# PROPÓSITO:
# - Excepción de auth controlada para mapear a tu envelope global.
#
# POR QUÉ:
# - FastAPI dependencies necesitan "cortar" el request lanzando excepción.
# - Pero queremos mantener codes estables y que REST/UI decida msg.
# ======================================================================

from __future__ import annotations


class AuthException(Exception):
    """
    Excepción controlada para auth.

    Contiene:
    - code estable (para presentación)
    - http_status
    - meta opcional (debug/auditoría)
    """

    def __init__(self, *, code: str, http_status: int, meta: dict | None = None):
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.meta = meta or {}