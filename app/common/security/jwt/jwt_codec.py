# ======================================================================
# app/common/security/jwt/jwt_codec.py
# -*- coding: utf-8 -*-
#
# PROPÓSITO:
# - Encapsular el "cómo" se crea y valida un JWT (encode/decode).
#
# POR QUÉ:
# - Evita que la lógica de JWT se replique en múltiples módulos (DRY).
# - Mantiene el JWT aislado de FastAPI y de DB (separación de concerns).
#
# PATRÓN APLICADO:
# - Codec / Adapter (envoltorio): abstrae la librería subyacente (python-jose).
#   Si mañana migras a PyJWT, se cambia este archivo y listo.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt


# ======================================================================
# 1) Error de dominio técnico (no UI)
# ======================================================================
class JwtCodecError(Exception):
    """
    Error controlado para tokens inválidos o expirados.

    POR QUÉ:
    - No queremos que capas superiores dependan de excepciones de librería.
    - La capa REST puede mapear esto a 401 de forma consistente.
    """

    pass


# ======================================================================
# 2) create_access_token
# ======================================================================
def create_access_token(
    *,
    secret_key: str,
    algorithm: str,
    ttl_seconds: int,
    claims: Dict[str, Any],
) -> str:
    """
    Genera un JWT agregando timestamps estándar.

    PARÁMETROS (intención):
    - secret_key: clave usada para firmar (HS256).
    - algorithm: algoritmo permitido (debe ser fijo para evitar confusiones).
    - ttl_seconds: TTL del token (controla duración del access token).
    - claims: claims de identidad mínima (ej. sub, role, jti).

    DECISIÓN DE SEGURIDAD:
    - Siempre añadimos:
      - iat: issued-at
      - exp: expiration
    - Esto evita tokens "eternos" y facilita auditoría.
    """

    # ------------------------------------------------------------------
    # 1) Calcular tiempos (UTC siempre)
    # ------------------------------------------------------------------
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=ttl_seconds)

    # ------------------------------------------------------------------
    # 2) Construir payload final
    # - Copiamos claims para no mutar el dict externo (defensivo).
    # ------------------------------------------------------------------
    payload = dict(claims)
    payload["iat"] = int(now.timestamp())
    payload["exp"] = int(exp.timestamp())

    # ------------------------------------------------------------------
    # 3) Firmar y retornar token
    # ------------------------------------------------------------------
    return jwt.encode(payload, secret_key, algorithm=algorithm)


# ======================================================================
# 3) decode_access_token
# ======================================================================
def decode_access_token(
    *,
    token: str,
    secret_key: str,
    algorithm: str,
) -> Dict[str, Any]:
    """
    Decodifica y valida un JWT.

    VALIDACIONES QUE OCURREN AQUÍ (por librería):
    - Firma (secret_key + algorithm)
    - Expiración (exp)

    POR QUÉ:
    - La verificación criptográfica pertenece a este nivel (codec).
    - La validación "de sesión" (jti contra DB) NO va aquí, va en users/auth.
    """

    # ------------------------------------------------------------------
    # 1) Intentar decodificar y validar
    # ------------------------------------------------------------------
    try:
        return jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as exc:
        # --------------------------------------------------------------
        # 2) Normalizar error hacia JwtCodecError
        # - Evita propagar tipos de error de librería
        # - Aísla dependencias externas
        # --------------------------------------------------------------
        raise JwtCodecError("Invalid or expired token") from exc