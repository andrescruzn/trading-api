# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/password_hasher.py
#
# PROPÓSITO:
# - Hashing seguro de passwords con bcrypt.
#
# MIGRACIÓN TRANSPARENTE:
# - Soporta verificación dual (bcrypt + sha1 legacy).
# - Al verificar exitosamente con sha1, indica que necesita rehash.
# - El service decide si actualiza el hash en DB.
#
# SEGURIDAD:
# - bcrypt con cost factor 12 (recomendado para 2024+).
# - SHA1 solo para compatibilidad con passwords existentes.
# ======================================================================

from __future__ import annotations

import hashlib
from typing import Tuple

import bcrypt


# ======================================================================
# Funciones principales
# ======================================================================

def hash_password(password: str) -> str:
    """
    Hashea password con bcrypt.

    Decisiones:
    - Cost factor 12: balance entre seguridad y performance.
    - Retorna string UTF-8 para guardar en VARCHAR.

    Retorna:
    - Hash bcrypt con prefijo $2b$ (60 caracteres).
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, stored_hash: str) -> Tuple[bool, bool]:
    """
    Verifica password contra hash almacenado.

    Soporta:
    - bcrypt ($2b$, $2a$, $2y$) - 60 caracteres
    - sha1 legacy - 40 caracteres hex

    Retorna:
    - Tuple[is_valid, needs_rehash]
    - needs_rehash=True si el password era válido pero usa sha1 legacy.

    Ejemplo de uso en service:
        is_valid, needs_rehash = verify_password(password, user.password_hash)
        if not is_valid:
            return fail("INVALID_CREDENTIALS")
        if needs_rehash:
            user.password_hash = hash_password(password)
    """
    # --------------------------------------------------------------
    # 1) Detectar bcrypt por prefijo estándar
    # --------------------------------------------------------------
    if stored_hash.startswith(("$2b$", "$2a$", "$2y$")):
        try:
            is_valid = bcrypt.checkpw(
                password.encode("utf-8"),
                stored_hash.encode("utf-8"),
            )
            return (is_valid, False)
        except (ValueError, TypeError):
            # Hash corrupto o inválido
            return (False, False)

    # --------------------------------------------------------------
    # 2) Fallback a SHA1 legacy (40 chars hex)
    # --------------------------------------------------------------
    if len(stored_hash) == 40 and _is_hex(stored_hash):
        sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest()
        is_valid = sha1_hash == stored_hash.lower()
        # Si es válido, necesita migrar a bcrypt
        return (is_valid, is_valid)

    # --------------------------------------------------------------
    # 3) Formato desconocido -> inválido
    # --------------------------------------------------------------
    return (False, False)


# ======================================================================
# Helpers internos
# ======================================================================

def _is_hex(s: str) -> bool:
    """Verifica si un string es hexadecimal válido."""
    try:
        int(s, 16)
        return True
    except ValueError:
        return False
