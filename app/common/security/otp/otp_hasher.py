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
# - Soporta migración desde SHA1 legacy.
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
from typing import Tuple


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
    Verifica OTP contra hash almacenado.

    Soporta:
    - HMAC-SHA256 (64 chars) - nuevo formato
    - SHA1 (40 chars) - legacy, para migración

    Parámetros:
    - otp: código OTP ingresado por usuario
    - stored_hash: hash almacenado en DB
    - secret_key: clave secreta (usa JWT_SECRET_KEY si no se proporciona)

    Retorna:
    - True si el OTP es válido

    Seguridad:
    - Usa comparación de tiempo constante para prevenir timing attacks.
    """
    if not otp or not stored_hash:
        return False

    # Detectar formato por longitud
    if len(stored_hash) == 64:
        # HMAC-SHA256 (nuevo)
        computed = hash_otp(otp, secret_key)
        return hmac.compare_digest(computed, stored_hash)

    elif len(stored_hash) == 40:
        # SHA1 legacy (migración)
        computed = hash_otp_sha1_hex(otp)
        return hmac.compare_digest(computed, stored_hash.lower())

    return False


def verify_otp_hash_with_migration(
    otp: str,
    stored_hash: str,
    secret_key: str | None = None,
) -> Tuple[bool, bool]:
    """
    Verifica OTP y detecta si necesita migración.

    Retorna:
    - Tuple[is_valid, needs_migration]
    - needs_migration=True si el hash es SHA1 legacy

    Uso:
        is_valid, needs_migration = verify_otp_hash_with_migration(otp, stored)
        if is_valid and needs_migration:
            user.otp_code = hash_otp(otp)  # Actualizar a HMAC
    """
    if not otp or not stored_hash:
        return (False, False)

    # HMAC-SHA256 (nuevo)
    if len(stored_hash) == 64:
        computed = hash_otp(otp, secret_key)
        is_valid = hmac.compare_digest(computed, stored_hash)
        return (is_valid, False)

    # SHA1 legacy
    if len(stored_hash) == 40:
        computed = hash_otp_sha1_hex(otp)
        is_valid = hmac.compare_digest(computed, stored_hash.lower())
        return (is_valid, is_valid)  # needs_migration si es válido

    return (False, False)


# ======================================================================
# Legacy (deprecado, solo para migración)
# ======================================================================

def hash_otp_sha1_hex(otp: str) -> str:
    """
    [DEPRECADO] Hashea OTP con SHA1 hex.

    Solo usar para verificar OTPs legacy durante migración.
    Para nuevos OTPs, usar hash_otp().
    """
    return hashlib.sha1(otp.encode("utf-8")).hexdigest()


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
