# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/otp/otp_hasher.py
#
# PROPÓSITO:
# - Hashear OTP antes de guardarlo en DB.
# - Verificar OTP ingresado contra hash almacenado.
#
# SEGURIDAD:
# - Usa HMAC-SHA256 con secret key (no vulnerable a rainbow tables).
# - Comparación de tiempo constante para prevenir timing attacks.
#
# USO:
#     from app.common.security.otp import hash_otp, verify_otp_hash
#
#     # Al generar OTP
#     hashed = hash_otp(otp_plain)
#     user.otp_code = hashed
#
#     # Al verificar OTP
#     is_valid = verify_otp_hash(otp_input, user.otp_code)
# ======================================================================

from __future__ import annotations

import hashlib
import hmac


# ======================================================================
# Funciones principales (HMAC-SHA256)
# ======================================================================

def hash_otp(otp: str, secret_key: str | None = None) -> str:
    """
    Hashea OTP con HMAC-SHA256.

    Parámetros:
    - otp: código OTP en texto plano
    - secret_key: clave secreta (usa JWT_SECRET_KEY si no se proporciona)

    Retorna:
    - Hash HMAC-SHA256 en hexadecimal (64 caracteres)

    Seguridad:
    - HMAC previene ataques de rainbow tables.
    - Usa secret key del sistema para mayor protección.
    """
    key = _get_secret_key(secret_key)

    return hmac.new(
        key.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp_hash(otp: str, stored_hash: str, secret_key: str | None = None) -> bool:
    """
    Verifica OTP contra hash HMAC-SHA256 almacenado.

    Parámetros:
    - otp: código OTP ingresado por usuario
    - stored_hash: hash almacenado en DB (64 caracteres hex)
    - secret_key: clave secreta (usa JWT_SECRET_KEY si no se proporciona)

    Retorna:
    - True si el OTP es válido

    Seguridad:
    - Usa comparación de tiempo constante para prevenir timing attacks.
    """
    if not otp or not stored_hash:
        return False

    # --------------------------------------------------------------
    # Validar formato esperado (HMAC-SHA256 = 64 chars hex)
    # --------------------------------------------------------------
    if len(stored_hash) != 64:
        return False

    # --------------------------------------------------------------
    # Comparar con tiempo constante
    # --------------------------------------------------------------
    computed = hash_otp(otp, secret_key)
    return hmac.compare_digest(computed, stored_hash)


# ======================================================================
# Helper interno
# ======================================================================

def _get_secret_key(secret_key: str | None = None) -> str:
    """Obtiene secret key para HMAC."""
    if secret_key:
        return secret_key

    # Lazy import para evitar ciclos
    from app.common.config import settings
    return settings.JWT_SECRET_KEY
