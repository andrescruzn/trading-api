# -*- coding: utf-8 -*-

# ======================================================================
# app/common/audit/audit_sanitizer.py
#
# PROPÓSITO:
# - Redactar campos sensibles de payloads antes de persistir en BD.
# - Nunca lanza excepciones — retorna None si el body no es JSON válido.
#
# CAMPOS REDACTADOS:
# - Request:  password, current_password, new_password, otp_code, token
# - Response: token, access_token (en root y en data{})
# ======================================================================

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

# ======================================================================
# Constantes
# ======================================================================

_REDACTED = "***REDACTED***"

_REQUEST_SENSITIVE_FIELDS = frozenset({
    "password",
    "current_password",
    "new_password",
    "otp_code",
    "token",
})

_RESPONSE_SENSITIVE_FIELDS = frozenset({
    "token",
    "access_token",
})


# ======================================================================
# Helpers
# ======================================================================

def _redact_fields(data: dict, fields: frozenset[str]) -> dict:
    """
    Reemplaza los valores de campos sensibles por _REDACTED.
    Mantiene las claves para saber que el campo vino en el payload.
    """
    result = dict(data)
    for key in fields:
        if key in result:
            result[key] = _REDACTED
    return result


# ======================================================================
# API pública
# ======================================================================

def sanitize_request(body_bytes: bytes) -> dict | None:
    """
    Parsea y sanitiza el body de un request HTTP.

    - Si vacío o no-JSON → retorna None.
    - Si es JSON → redacta campos sensibles y retorna el dict.
    """
    if not body_bytes:
        return None

    try:
        data = json.loads(body_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    return _redact_fields(data, _REQUEST_SENSITIVE_FIELDS)


def sanitize_response(body_bytes: bytes) -> dict | None:
    """
    Parsea y sanitiza el body de una respuesta HTTP.

    - Si vacío, HTML o no-JSON → retorna None.
    - Si es JSON → redacta campos sensibles en root y en data{}.
    """
    if not body_bytes:
        return None

    try:
        data = json.loads(body_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    # Redactar campos en root
    result = _redact_fields(data, _RESPONSE_SENSITIVE_FIELDS)

    # Redactar campos dentro de data{} si es un dict
    if isinstance(result.get("data"), dict):
        result["data"] = _redact_fields(result["data"], _RESPONSE_SENSITIVE_FIELDS)

    return result
