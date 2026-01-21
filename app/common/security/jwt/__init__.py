# ======================================================================
# app/common/security/jwt/__init__.py
# -*- coding: utf-8 -*-
#
# PROPÓSITO:
# - Barrel exports para imports limpios.
#
# POR QUÉ:
# - Evita rutas largas en imports.
# - Reduce duplicación y ordena la API pública del submódulo JWT.
# ======================================================================

from .jwt_settings import JwtSettings, load_jwt_settings
from .jwt_codec import create_access_token, decode_access_token, JwtCodecError
from .jwt_dependency import JwtIdentity, require_jwt_identity, token_required

__all__ = [
    "JwtSettings",
    "load_jwt_settings",
    "create_access_token",
    "decode_access_token",
    "JwtCodecError",
    "JwtIdentity",
    "require_jwt_identity",
    "token_required",
]