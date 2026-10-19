# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/scheduler/scheduler_lock.py
#
# PROPÓSITO:
# - Que el scheduler corra en UN solo proceso aunque uvicorn/gunicorn
#   levante varios workers (cada worker arranca su hilo en el lifespan).
#   Sin esto, cada worker descargaría velas y —con la ejecución
#   automática— generaría señales y órdenes duplicadas.
#
# DISEÑO (elección de líder con MySQL):
# - GET_LOCK es por conexión: el worker que lo obtiene guarda esa conexión
#   abierta y es el líder mientras viva. Si el proceso muere o la conexión
#   se corta, MySQL libera el lock y otro worker lo toma en su siguiente
#   ciclo.
# - Cada ciclo confirma que sigue siendo el dueño (IS_USED_LOCK =
#   CONNECTION_ID()); eso además mantiene viva la conexión.
# ======================================================================

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.extensions.db import engine

logger = logging.getLogger(__name__)

_LOCK_NAME = "trading-app-scheduler"


class SchedulerLock:
    """Lock de líder del scheduler, basado en GET_LOCK de MySQL."""

    def __init__(self, name: str = _LOCK_NAME):
        self._name = name
        self._conn: Connection | None = None

    def acquire(self) -> bool:
        """True si este proceso es (o acaba de convertirse en) el líder."""
        try:
            if self._conn is not None:
                owner = self._conn.execute(
                    text("SELECT IS_USED_LOCK(:name) = CONNECTION_ID()"),
                    {"name": self._name},
                ).scalar()
                # Cerrar la transacción implícita: no dejar un snapshot abierto
                self._conn.commit()
                if owner == 1:
                    return True
                self._close()

            conn = engine.connect()
            got = conn.execute(text("SELECT GET_LOCK(:name, 0)"), {"name": self._name}).scalar()
            conn.commit()
            if got == 1:
                self._conn = conn
                logger.info("[Scheduler] Este proceso es el líder (lock %s).", self._name)
                return True
            conn.close()
            return False
        except Exception:
            logger.exception("[Scheduler] No se pudo verificar el lock; se omite el ciclo.")
            self._close()
            return False

    def release(self) -> None:
        if self._conn is None:
            return
        try:
            self._conn.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": self._name})
        except Exception:
            logger.warning("[Scheduler] No se pudo liberar el lock explícitamente.")
        self._close()

    def _close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
