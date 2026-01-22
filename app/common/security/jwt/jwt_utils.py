# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/jwt/jwt_utils.py
#
# PROPÓSITO:
# - Emisión y decodificación JWT en un solo lugar.
#
# CONTRATO (TU PROYECTO):
# - sub es dict: {"user_id": int}
# - incluye jti para invalidación por DB (users.token_current_jti)
# - type="access"
#
# NOTA IMPORTANTE (python-jose):
# - Por estándar JWT, "sub" suele ser string.
# - python-jose valida eso por defecto y revienta si "sub" es dict.
# - Como TU contrato usa dict, desactivamos verify_sub al decodificar.
# ======================================================================

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt


class JwtCodecError(Exception):
    """
    Error controlado para tokens inválidos/expirados.
    """
    pass


def generate_jti() -> str:
    """
    Genera un identificador único para el token (JTI).
    """
    return uuid.uuid4().hex


def create_access_token(
    *,
    subject: Dict[str, Any],
    secret_key: str,
    expires_delta: timedelta,
    algorithm: str = "HS256",
    jti: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Crea access token.

    Retorna un paquete para que services puedan:
    - guardar jti en DB
    - retornar token + expires_at
    """
    now = datetime.now(timezone.utc)
    exp = now + expires_delta
    token_jti = jti or generate_jti()

    payload = {
        # --------------------------------------------------------------
        # TU CONTRATO:
        # - subject es dict, no string
        # --------------------------------------------------------------
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": token_jti,
        "type": "access",
    }

    encoded = jwt.encode(payload, secret_key, algorithm=algorithm)

    return {
        "token": encoded,
        "jti": token_jti,
        "expires_at": exp,
    }


def decode_access_token(
    *,
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> Dict[str, Any]:
    """
    Decodifica y valida firma/exp del JWT.

    CLAVE:
    - Desactivamos verify_sub porque "sub" en TU token es dict.
    - Seguimos validando:
      - firma (signature)
      - expiración (exp)
    """
    try:
        return jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={
                # ------------------------------------------------------
                # Seguridad base (dejamos todo ON)
                # ------------------------------------------------------
                "verify_signature": True,
                "verify_exp": True,
                # ------------------------------------------------------
                # ✅ TU CONTRATO: sub es dict, no string
                # ------------------------------------------------------
                "verify_sub": False,
            },
        )
    except JWTError as exc:
        raise JwtCodecError("Invalid or expired token") from exc