# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/scheduler/scheduler_runner.py
#
# PROPÓSITO:
# - Gestionar el hilo de fondo que ejecuta run_cycle() periódicamente y,
#   una vez al día, refresh_explorer() (velas 1d del explorador).
# - Expone start() / stop() para integrarse con el lifespan de FastAPI.
#
# DISEÑO:
# - threading.Thread con daemon=True: el proceso principal puede
#   terminar sin esperar al scheduler (stop() hace join explícito).
# - threading.Event como señal de parada: permite que el sleep sea
#   interrumpible (no bloquea el shutdown hasta que el sleep termine).
# - Con varios workers, solo el que tiene el lock de MySQL (SchedulerLock)
#   ejecuta los ciclos; los demás esperan su turno por si el líder cae.
# ======================================================================

from __future__ import annotations

import logging
import threading
import time

from app.common.config import settings

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_scheduler_thread: threading.Thread | None = None

# Cada cuánto se refrescan las velas diarias del explorador
_EXPLORER_REFRESH_SECONDS = 86400


def _run_loop() -> None:
    """
    Loop principal del hilo scheduler.

    Ejecuta run_cycle() y luego espera SCHEDULER_INTERVAL_SECONDS antes
    de la siguiente iteración. El Event permite que stop() interrumpa
    la espera de forma limpia.
    """
    # Import diferido para evitar importaciones circulares al arrancar
    from app.modules.scheduler.execution_cycle import run_execution_cycle
    from app.modules.scheduler.scheduler_lock import SchedulerLock
    from app.modules.scheduler.scheduler_service import refresh_explorer, run_cycle

    lock = SchedulerLock()

    logger.info(
        "[Scheduler] Iniciado — intervalo=%ds retención=%d velas",
        settings.SCHEDULER_INTERVAL_SECONDS,
        settings.SCHEDULER_RETENTION_CANDLES,
    )

    # monotonic: no le afectan los cambios de hora del sistema.
    # None = refrescar en la primera vuelta (al arrancar la API).
    last_explorer_refresh: float | None = None

    while not _stop_event.is_set():
        # Solo el líder trabaja; el resto vuelve a intentarlo en el siguiente ciclo
        if not lock.acquire():
            _stop_event.wait(timeout=settings.SCHEDULER_INTERVAL_SECONDS)
            continue

        now = time.monotonic()
        if (
            last_explorer_refresh is None
            or now - last_explorer_refresh >= _EXPLORER_REFRESH_SECONDS
        ):
            last_explorer_refresh = now
            refresh_explorer()

        try:
            run_cycle()
        except Exception:
            logger.exception("[Scheduler] Error no controlado en ciclo.")

        # Después de velas e indicadores: señales automáticas, caducidad,
        # SL/TP y Telegram (cada paso aislado dentro del ciclo)
        run_execution_cycle()

        # Espera interrumpible: si stop() activa el evento, wait() retorna
        # antes de que expire el timeout y el loop termina limpiamente.
        _stop_event.wait(timeout=settings.SCHEDULER_INTERVAL_SECONDS)

    lock.release()
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
