# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/crypto_hash.py
#
# PROPÓSITO:
# - Hashing legacy (SHA1 hex) centralizado.
#
# NOTA DE SEGURIDAD:
# - SHA1 no es ideal para passwords (mejor bcrypt/argon2).
# - Pero como tu sistema es legacy, lo centralizamos para consistencia.
# ======================================================================

from __future__ import annotations

import hashlib


def sha1_hex(raw: str) -> str:
    """
    Retorna SHA1 hex de un string UTF-8.
    """
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()