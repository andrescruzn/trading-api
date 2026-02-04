# -*- coding: utf-8 -*-

# ======================================================================
# app/common/logging/logger.py
#
# PROPÓSITO:
# - Logging estructurado en formato JSON.
# - Centraliza configuración de logs para toda la aplicación.
#
# FORMATO:
# - JSON en producción (para parsing en ELK, CloudWatch, etc.)
# - Texto legible en desarrollo
#
# USO:
#     from app.common.logging import get_logger, log_auth_event
#
#     logger = get_logger(__name__)
#     logger.info("Mensaje", extra={"user_id": 123})
#
#     log_auth_event("login_success", user_id=123, email="test@test.com")
# ======================================================================

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


# ======================================================================
# Context variables (request-scoped)
# ======================================================================

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id: ContextVar[Optional[int]] = ContextVar("user_id", default=None)


def get_request_id() -> Optional[str]:
    """Obtiene request_id del contexto actual."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Establece request_id en el contexto."""
    _request_id.set(request_id)


def generate_request_id() -> str:
    """Genera un nuevo request_id."""
    return uuid.uuid4().hex[:16]


def get_context_user_id() -> Optional[int]:
    """Obtiene user_id del contexto actual."""
    return _user_id.get()


def set_context_user_id(user_id: int) -> None:
    """Establece user_id en el contexto."""
    _user_id.set(user_id)


def clear_context() -> None:
    """Limpia el contexto (al final del request)."""
    _request_id.set(None)
    _user_id.set(None)


# ======================================================================
# JSON Formatter
# ======================================================================

class JsonFormatter(logging.Formatter):
    """
    Formatter que produce logs en formato JSON.

    Campos incluidos:
    - timestamp: ISO 8601 UTC
    - level: nivel del log
    - logger: nombre del logger
    - message: mensaje
    - request_id: ID del request (si existe)
    - user_id: ID del usuario (si existe)
    - extra: campos adicionales
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Agregar contexto si existe
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        user_id = get_context_user_id()
        if user_id:
            log_data["user_id"] = user_id

        # Agregar campos extra (excluyendo los estándar de logging)
        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "taskName", "message",
        }

        extra = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_")
        }

        if extra:
            log_data["extra"] = extra

        # Agregar exception si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class DevFormatter(logging.Formatter):
    """
    Formatter legible para desarrollo.

    Formato: [TIMESTAMP] LEVEL logger - message {extra}
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        base = f"[{timestamp}] {record.levelname:8} {record.name} - {record.getMessage()}"

        # Agregar contexto
        context_parts = []
        request_id = get_request_id()
        if request_id:
            context_parts.append(f"req={request_id}")

        user_id = get_context_user_id()
        if user_id:
            context_parts.append(f"user={user_id}")

        if context_parts:
            base += f" [{', '.join(context_parts)}]"

        # Agregar exception
        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


# ======================================================================
# Configuración
# ======================================================================

def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """
    Configura logging para toda la aplicación.

    Parámetros:
    - level: nivel de logging (DEBUG, INFO, WARNING, ERROR)
    - json_format: usar formato JSON (True para prod, False para dev)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Limpiar handlers existentes
    root_logger.handlers.clear()

    # Crear handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Seleccionar formatter
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(DevFormatter())

    root_logger.addHandler(handler)

    # Reducir ruido de librerías
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado.

    Uso:
        logger = get_logger(__name__)
        logger.info("Mensaje")
    """
    return logging.getLogger(name)


# ======================================================================
# Funciones de logging de alto nivel
# ======================================================================

def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[int] = None,
) -> None:
    """
    Log de request HTTP.

    Uso en middleware o al final de cada request.
    """
    logger = get_logger("app.request")
    logger.info(
        f"{method} {path} -> {status_code}",
        extra={
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": round(duration_ms, 2),
            "user_id": user_id,
        },
    )


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log de error con contexto.
    """
    logger = get_logger("app.error")
    logger.error(
        str(error),
        extra={
            "error_type": type(error).__name__,
            "context": context or {},
        },
        exc_info=True,
    )


def log_auth_event(
    event: str,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    success: bool = True,
    reason: Optional[str] = None,
) -> None:
    """
    Log de evento de autenticación.

    Eventos:
    - login_password_success, login_password_failed
    - login_otp_requested, login_otp_success, login_otp_failed
    - logout, token_rotated
    - account_locked
    """
    logger = get_logger("app.auth")
    level = logging.INFO if success else logging.WARNING

    logger.log(
        level,
        f"Auth event: {event}",
        extra={
            "event": event,
            "auth_user_id": user_id,
            "auth_email": email,
            "success": success,
            "reason": reason,
        },
    )


def log_business_event(
    event: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log de evento de negocio.

    Uso para auditoría de acciones importantes.
    """
    logger = get_logger("app.business")
    logger.info(
        f"Business event: {event}",
        extra={
            "event": event,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": data or {},
        },
    )
