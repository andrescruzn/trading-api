# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/password_hasher.py
#
# PROPÓSITO:
# - Hashing seguro de passwords con bcrypt.
#
# SEGURIDAD:
# - bcrypt con cost factor 12 (recomendado para 2024+).
# - Sin soporte legacy SHA1 (aplicación nueva, sin usuarios existentes).
# ======================================================================

from __future__ import annotations

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


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifica password contra hash bcrypt almacenado.

    Parámetros:
    - password: password en texto plano
    - stored_hash: hash bcrypt almacenado ($2b$, $2a$, $2y$)

    Retorna:
    - True si el password es válido, False en caso contrario.

    Seguridad:
    - bcrypt usa comparación de tiempo constante internamente.
    """
    # --------------------------------------------------------------
    # Validar que es un hash bcrypt válido
    # --------------------------------------------------------------
    if not stored_hash.startswith(("$2b$", "$2a$", "$2y$")):
        return False

    # --------------------------------------------------------------
    # Verificar password contra bcrypt
    # --------------------------------------------------------------
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Hash corrupto o inválido
        return False
