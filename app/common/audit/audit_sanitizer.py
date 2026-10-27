# -*- coding: utf-8 -*-

# ======================================================================
# app/common/audit/audit_sanitizer.py
#
# PROPÓSITO:
# - Redactar campos sensibles de payloads antes de persistir en BD.
# - Nunca lanza excepciones — retorna None si el body no es JSON válido.
#
# CAMPOS REDACTADOS (en cualquier nivel de anidación, dicts y listas):
# - Request:  password, otp_code, token, credenciales de exchange
#             (api_key, api_secret, passphrase…) y URLs de webhook
#             (suelen llevar el token en la ruta: Slack, Discord).
# - Response: token, access_token, otp_code (dev), enc_creds.
#
# RESPUESTAS (summarize_response, la que usa el middleware):
# - Éxito (< 400): solo `msg` y `errorCode` del envelope; el `data` no aporta
#   a la auditoría y es lo que más pesa (listas, velas, saldos).
# - Error (>= 400): el envelope completo redactado, si cabe en
#   MAX_BODY_BYTES; si no, solo `msg` y `errorCode`.
#
# NOTA:
# - La comparación de claves no distingue mayúsculas (`apiKey` == `apikey`).
# ======================================================================

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ======================================================================
# Constantes
# ======================================================================

_REDACTED = "***REDACTED***"

# Límite de body a auditar (10 KB): requests más grandes (p. ej. comprobantes
# en base64) no se guardan, y las respuestas de error se reducen al resumen.
MAX_BODY_BYTES = 10 * 1024

# Claves del envelope {msg, errorCode, data} que se guardan como resumen.
_SUMMARY_KEYS = ("msg", "errorCode")

# Límite de profundidad: un JSON más anidado se corta (evita recursión infinita).
_MAX_DEPTH = 20

_REQUEST_SENSITIVE_FIELDS = frozenset({
    "password",
    "current_password",
    "new_password",
    "otp_code",
    "token",
    "access_token",
    "api_key",
    "apikey",
    "api_secret",
    "secret",
    "passphrase",
    "private_key",
    "enc_creds",
    "credentials_ref",
    "webhook",
    "webhook_url",
    "authorization",
})

_RESPONSE_SENSITIVE_FIELDS = frozenset({
    "token",
    "access_token",
    "otp_code",
    "enc_creds",
    "credentials_ref",
    "link_url",
    "webhook",
    "webhook_url",
})


# ======================================================================
# Helpers
# ======================================================================

def _redact(value: Any, fields: frozenset[str], depth: int = 0) -> Any:
    """
    Recorre dicts y listas y reemplaza los valores de campos sensibles por
    _REDACTED. Mantiene las claves para saber que el campo vino en el payload.
    """
    if depth > _MAX_DEPTH:
        return _REDACTED

    if isinstance(value, dict):
        return {
            key: (
                _REDACTED
                if isinstance(key, str) and key.lower() in fields
                else _redact(item, fields, depth + 1)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_redact(item, fields, depth + 1) for item in value]

    return value


def _parse_object(body_bytes: bytes) -> dict | None:
    """JSON → dict; None si está vacío, no es JSON o no es un objeto."""
    if not body_bytes:
        return None

    try:
        data = json.loads(body_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    return data if isinstance(data, dict) else None


# ======================================================================
# API pública
# ======================================================================

def redact_request_data(data: Any) -> Any:
    """Redacta un payload de request ya parseado (lo usa el script de purga)."""
    return _redact(data, _REQUEST_SENSITIVE_FIELDS)


def redact_response_data(data: Any) -> Any:
    """Redacta un payload de respuesta ya parseado (lo usa el script de purga)."""
    return _redact(data, _RESPONSE_SENSITIVE_FIELDS)


def sanitize_request(body_bytes: bytes) -> dict | None:
    """
    Parsea y sanitiza el body de un request HTTP.

    - Si vacío o no-JSON → retorna None.
    - Si es JSON → redacta campos sensibles (a cualquier nivel) y retorna el dict.
    """
    data = _parse_object(body_bytes)
    if data is None:
        return None
    return _redact(data, _REQUEST_SENSITIVE_FIELDS)


def sanitize_response(body_bytes: bytes) -> dict | None:
    """
    Parsea y sanitiza el body de una respuesta HTTP.

    - Si vacío, HTML o no-JSON → retorna None.
    - Si es JSON → redacta campos sensibles a cualquier nivel.
    """
    data = _parse_object(body_bytes)
    if data is None:
        return None
    return _redact(data, _RESPONSE_SENSITIVE_FIELDS)


def summarize_response(body_bytes: bytes, status_code: int) -> dict | None:
    """
    Resume el body de una respuesta para la auditoría.

    - Éxito (< 400) → solo `msg` y `errorCode` del envelope.
    - Error (>= 400) → el JSON redactado completo si pesa ≤ MAX_BODY_BYTES;
      si pesa más, solo `msg` y `errorCode`.
    - Vacío, HTML o no-JSON → None.
    """
    data = _parse_object(body_bytes)
    if data is None:
        return None

    if status_code >= 400 and len(body_bytes) <= MAX_BODY_BYTES:
        return _redact(data, _RESPONSE_SENSITIVE_FIELDS)

    summary = {key: data[key] for key in _SUMMARY_KEYS if key in data}
    return summary or None
