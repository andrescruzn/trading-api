# -*- coding: utf-8 -*-

# ======================================================================
# app/common/logging/__init__.py
#
# Barrel exports del módulo de logging.
# ======================================================================

from .logger import (
    get_logger,
    configure_logging,
    log_request,
    log_error,
    log_auth_event,
    log_business_event,
    set_request_id,
    set_context_user_id,
)
from .middleware import LoggingMiddleware

__all__ = [
    # Logger
    "get_logger",
    "configure_logging",

    # Funciones de log
    "log_request",
    "log_error",
    "log_auth_event",
    "log_business_event",

    # Contexto
    "set_request_id",
    "set_context_user_id",

    # Middleware
    "LoggingMiddleware",
]
