# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/scheduler/scheduler_runner.py
#
# PROPÓSITO:
# - Gestionar el hilo de fondo que ejecuta run_cycle() periódicamente.
# - Expone start() / stop() para integrarse con el lifespan de FastAPI.
#
# DISEÑO:
# - threading.Thread con daemon=True: el proceso principal puede
#   terminar sin esperar al scheduler (stop() hace join explícito).
# - threading.Event como señal de parada: permite que el sleep sea
#   interrumpible (no bloquea el shutdown hasta que el sleep termine).
# ======================================================================

from __future__ import annotations

import logging
import threading
import time

from app.common.config import settings

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_scheduler_thread: threading.Thread | None = None


def _run_loop() -> None:
    """
    Loop principal del hilo scheduler.

    Ejecuta run_cycle() y luego espera SCHEDULER_INTERVAL_SECONDS antes
    de la siguiente iteración. El Event permite que stop() interrumpa
    la espera de forma limpia.
    """
    # Import diferido para evitar importaciones circulares al arrancar
    from app.modules.scheduler.scheduler_service import run_cycle

    logger.info(
        "[Scheduler] Iniciado — intervalo=%ds retención=%d velas",
        settings.SCHEDULER_INTERVAL_SECONDS,
        settings.SCHEDULER_RETENTION_CANDLES,
    )

    while not _stop_event.is_set():
        try:
            run_cycle()
        except Exception:
            logger.exception("[Scheduler] Error no controlado en ciclo.")

        # Espera interrumpible: si stop() activa el evento, wait() retorna
        # antes de que expire el timeout y el loop termina limpiamente.
        _stop_event.wait(timeout=settings.SCHEDULER_INTERVAL_SECONDS)

    logger.info("[Scheduler] Detenido.")


def start() -> None:
    """
    Arranca el hilo scheduler si SCHEDULER_ENABLED=true.

    Seguro para llamar múltiples veces: si ya está corriendo, no hace nada.
    """
    global _scheduler_thread

    if not settings.SCHEDULER_ENABLED:
        logger.info("[Scheduler] Deshabilitado (SCHEDULER_ENABLED=false).")
        return

    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        logger.warning("[Scheduler] Ya está corriendo, ignorando start().")
        return

    _stop_event.clear()
    _scheduler_thread = threading.Thread(
        target=_run_loop,
        name="trading-scheduler",
        daemon=True,
    )
    _scheduler_thread.start()


def stop() -> None:
    """
    Señala al hilo que debe detenerse y espera hasta 10 s a que termine.

    Se llama desde el shutdown de FastAPI (lifespan teardown).
    """
    global _scheduler_thread

    _stop_event.set()

    if _scheduler_thread is not None:
        _scheduler_thread.join(timeout=10)
        _scheduler_thread = None

    logger.info("[Scheduler] Apagado completo.")
