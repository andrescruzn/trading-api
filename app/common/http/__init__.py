# -*- coding: utf-8 -*-

# ======================================================================
# app/common/http/__init__.py
#
# Barrel exports del paquete HTTP (presentación).
#
# CONTENIDO:
# - send(): función de bajo nivel para respuestas JSON
# - build_*(): funciones de alto nivel para construir respuestas
# ======================================================================

from .http_responder import send
from .response_builder import (
    # Errores
    build_error_response,
    build_internal_error_response,
    # Éxito
    build_success_response,
    build_created_response,
    build_data_response,
    # Listados
    build_list_response,
    build_paginated_response,
    # Autenticación (legacy: devuelve token en body)
    build_token_response,
    build_otp_required_response,
    # Autenticación con cookies HTTP-only (recomendado para SPA)
    build_cookie_auth_response,
    build_logout_response,
    # Helper
    build_from_service_result,
)

__all__ = [
    # Bajo nivel
    "send",

    # Errores
    "build_error_response",
    "build_internal_error_response",

    # Éxito
    "build_success_response",
    "build_created_response",
    "build_data_response",

    # Listados
    "build_list_response",
    "build_paginated_response",

    # Autenticación (legacy: devuelve token en body)
    "build_token_response",
    "build_otp_required_response",

    # Autenticación con cookies HTTP-only (recomendado para SPA)
    "build_cookie_auth_response",
    "build_logout_response",

    # Helper completo
    "build_from_service_result",
]
