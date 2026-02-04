# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/error_messages.py
#
# Mensajes de error para el módulo de autenticación.
#
# NOTA:
# - Usa AUTH_ERROR_MESSAGES de common/errors como base.
# - Solo agrega mensajes específicos si es necesario.
# ======================================================================

from app.common.errors import AUTH_ERROR_MESSAGES

# Re-exportar para uso local (incluye todos los mensajes de auth)
DEFAULT_AUTH_ERROR_MESSAGES = AUTH_ERROR_MESSAGES