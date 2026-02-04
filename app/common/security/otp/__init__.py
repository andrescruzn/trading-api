# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/otp/__init__.py
#
# Barrel exports del módulo OTP.
# ======================================================================

from .otp_generator import generate_numeric_otp
from .otp_hasher import (
    hash_otp,
    verify_otp_hash,
    hash_otp_sha1_hex,  # Deprecado, solo para migración
)

__all__ = [
    "generate_numeric_otp",
    "hash_otp",
    "verify_otp_hash",
    "hash_otp_sha1_hex",  # Deprecado
]