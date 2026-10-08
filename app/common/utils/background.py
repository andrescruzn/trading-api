# -*- coding: utf-8 -*-

# ======================================================================
# app/common/utils/background.py
#
# PROPÓSITO:
# - Ejecutar trabajo de I/O lento (SMTP, webhooks) fuera del request, para
#   que la respuesta no espere y su tiempo no revele nada (p. ej. si un
#   correo tiene cuenta en el login por OTP).
#
# NOTAS:
# - Pool de hilos del proceso: no sobrevive a un reinicio y no reintenta
#   por sí solo. El reintento lo decide quien encola (ver MailerService).
# - La tarea NO debe usar la Session del request: ya estará cerrada.
# - Excepciones no capturadas se registran en el log (no se pierden).
# ======================================================================

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="background")


def _log_failure(future: Future[Any]) -> None:
    """Registra la excepción de una tarea que terminó con error."""
    exc = future.exception()
    if exc is not None:
        logger.error("Background task failed", exc_info=exc)


def run_in_background(fn: Callable[..., Any], /, *args: Any, **kwargs: Any) -> None:
    """
    Encola `fn(*args, **kwargs)` en el pool de hilos y retorna de inmediato.
    """
    future = _executor.submit(fn, *args, **kwargs)
    future.add_done_callback(_log_failure)
