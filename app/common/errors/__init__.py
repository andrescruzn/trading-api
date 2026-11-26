# -*- coding: utf-8 -*-

# ======================================================================
# app/common/errors/__init__.py
#
# Barrel exports para handlers globales y mensajes de error.
# ======================================================================

from .errors import register_error_handlers
from .error_messages import (
    COMMON_ERROR_MESSAGES,
    AUTH_ERROR_MESSAGES,
    merge_error_messages,
)

__all__ = [
    # Handlers
    "register_error_handlers",

    # Mensajes de error
    "COMMON_ERROR_MESSAGES",
    "AUTH_ERROR_MESSAGES",
    "merge_error_messages",
]