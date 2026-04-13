# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/scheduler/scheduler_service.py
#
# PROPÓSITO:
# - Ejecutar un ciclo completo de actualización de datos de mercado:
#   1. Leer bots activos/pausados de la DB.
#   2. Por cada par único (symbol_id, timeframe_id): fetch de velas si
#      el timeframe venció o no hay datos aún.
#   3. Por cada tripla única (symbol_id, timeframe_id, feature_set_id):
#      calcular features si se obtuvieron velas nuevas.
#   4. Cleanup de candles y candle_features más allá del límite de
#      retención configurado.
#
# DISEÑO:
# - Sin nueva tabla en BD (Opción B): se deriva todo de los bots activos.
# - Cada operación usa su propia sesión SQLAlchemy (no comparte estado).
# - Errores aislados por par: un fallo no detiene los demás.
# ======================================================================

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.common.config import settings
from app.extensions.db.session import SessionLocal
from app.modules.bots.infrastructure.bot_model import BotModel
from app.modules.features.providers.feature_provider import FeatureServiceFactory
from app.modules.market.infrastructure.timeframe_model import TimeframeModel
from app.modules.market.providers.market_provider import MarketServiceFactory

logger = logging.getLogger(__name__)

# Límite de velas para carga inicial (sin datos previos)
_INITIAL_FETCH_LIMIT = 500
# Límite para actualizaciones incrementales (vela nueva + margen)
_INCREMENTAL_FETCH_LIMIT = 3


# ======================================================================
# Helpers de consulta
# ======================================================================

def _get_latest_candle_ts(
    session,
    symbol_id: int,
    timeframe_id: int,
) -> datetime | None:
    """Retorna el timestamp de la vela más reciente para el par dado."""
    result = session.execute(
        text(
            "SELECT MAX(ts) FROM candles "
            "WHERE symbol_id = :sid AND timeframe_id = :tid"
        ),
        {"sid": symbol_id, "tid": timeframe_id},
    ).scalar()

    if result is None:
        return None
    # MySQL devuelve datetime naive → normalizar a UTC aware
    if result.tzinfo is None:
        return result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def _should_fetch(
    latest_ts: datetime | None,
    timeframe_seconds: int,
) -> tuple[bool, int]:
    """
    Determina si hace falta descargar velas nuevas.

    Retorna (debe_fetchear, limit):
    - Sin velas en BD → carga inicial de 500 velas.
    - Última vela vencida (now - latest_ts >= timeframe) → incremental de 3.
    - Vela vigente → no hace falta.
    """
    if latest_ts is None:
        return True, _INITIAL_FETCH_LIMIT

    now = datetime.now(tz=timezone.utc)
    elapsed = (now - latest_ts).total_seconds()

    if elapsed >= timeframe_seconds:
        return True, _INCREMENTAL_FETCH_LIMIT

    return False, 0


# ======================================================================
# Helpers de cleanup
# ======================================================================

def _cleanup_candles(
    session,
    symbol_id: int,
    timeframe_id: int,
    retention: int,
) -> int:
    """
    Elimina velas más antiguas que el límite de retención.

    Conserva las últimas `retention` velas ordenadas por ts DESC.
    El subquery doble es necesario para MySQL (no permite self-reference
    directo en DELETE ... WHERE).
    """
    result = session.execute(
        text("""
            DELETE FROM candles
            WHERE symbol_id = :sid
              AND timeframe_id = :tid
              AND ts < (
                  SELECT ts FROM (
                      SELECT ts FROM candles
                      WHERE symbol_id = :sid
                        AND timeframe_id = :tid
                      ORDER BY ts DESC
                      LIMIT 1 OFFSET :offset
                  ) AS _cutoff
              )
        """),
        {"sid": symbol_id, "tid": timeframe_id, "offset": retention - 1},
    )
    session.commit()
    return result.rowcount


def _cleanup_candle_features(
    session,
    symbol_id: int,
    timeframe_id: int,
    feature_set_id: int,
    retention: int,
) -> int:
    """
    Elimina candle_features más antiguas que el límite de retención.

    Mismo criterio que _cleanup_candles, por tripla
    (symbol_id, timeframe_id, feature_set_id).
    """
    result = session.execute(
        text("""
            DELETE FROM candle_features
            WHERE symbol_id = :sid
              AND timeframe_id = :tid
              AND feature_set_id = :fsid
              AND ts < (
                  SELECT ts FROM (
                      SELECT ts FROM candle_features
                      WHERE symbol_id = :sid
                        AND timeframe_id = :tid
                        AND feature_set_id = :fsid
                      ORDER BY ts DESC
                      LIMIT 1 OFFSET :offset
                  ) AS _cutoff
              )
        """),
        {
            "sid": symbol_id,
            "tid": timeframe_id,
            "fsid": feature_set_id,
            "offset": retention - 1,
        },
    )
    session.commit()
    return result.rowcount


# ======================================================================
# Ciclo principal
# ======================================================================

def run_cycle() -> None:
    """
    Ejecuta un ciclo completo del scheduler:

    1. Lee bots con status IN ('running', 'paused').
    2. Agrupa pares únicos (symbol_id, timeframe_id) y consulta si
       sus velas están vigentes o necesitan fetch.
    3. Agrupa triplas únicas (symbol_id, timeframe_id, feature_set_id)
       para calcular features solo cuando hubo fetch exitoso.
    4. Limpia candles y candle_features más allá del retention limit.
    """
    retention = settings.SCHEDULER_RETENTION_CANDLES

    # ------------------------------------------------------------------
    # Paso 1: leer bots activos y construir los conjuntos de trabajo
    # ------------------------------------------------------------------
    session = SessionLocal()
    try:
        bots = (
            session.query(BotModel)
            .filter(BotModel.status.in_(["running", "paused"]))
            .all()
        )
        if not bots:
            logger.debug("[Scheduler] No hay bots activos. Ciclo omitido.")
            return

        # Pares únicos para fetch: (symbol_id, timeframe_id) → seconds
        fetch_pairs: dict[tuple[int, int], int] = {}
        for bot in bots:
            key = (bot.symbol_id, bot.timeframe_id)
            if key not in fetch_pairs:
                tf = (
                    session.query(TimeframeModel)
                    .filter(TimeframeModel.id == bot.timeframe_id)
                    .first()
                )
                if tf is not None:
                    fetch_pairs[key] = tf.seconds

        # Triplas únicas para calculate: (symbol_id, timeframe_id, feature_set_id)
        calc_triplets: set[tuple[int, int, int]] = {
            (bot.symbol_id, bot.timeframe_id, bot.feature_set_id)
            for bot in bots
            if bot.feature_set_id is not None
        }

        # Determinar qué pares necesitan fetch
        fetch_needed: dict[tuple[int, int], int] = {}
        for (symbol_id, tf_id), tf_seconds in fetch_pairs.items():
            latest_ts = _get_latest_candle_ts(session, symbol_id, tf_id)
            should, limit = _should_fetch(latest_ts, tf_seconds)
            if should:
                fetch_needed[(symbol_id, tf_id)] = limit

    finally:
        session.close()

    if not fetch_needed:
        logger.debug("[Scheduler] Todas las velas están vigentes. Ciclo omitido.")
        return

    # ------------------------------------------------------------------
    # Paso 2: fetch de velas por par
    # ------------------------------------------------------------------
    fetched_pairs: set[tuple[int, int]] = set()

    for (symbol_id, tf_id), limit in fetch_needed.items():
        session = SessionLocal()
        try:
            result = MarketServiceFactory(session).fetch_candles().fetch(
                symbol_id=symbol_id,
                timeframe_id=tf_id,
                limit=limit,
            )
            if result.success:
                fetched_pairs.add((symbol_id, tf_id))
                logger.info(
                    "[Scheduler] Fetch OK — symbol=%d tf=%d "
                    "rows=%d limit=%d",
                    symbol_id, tf_id,
                    result.data["rows_fetched"], limit,
                )
            else:
                logger.warning(
                    "[Scheduler] Fetch FAIL — symbol=%d tf=%d code=%s",
                    symbol_id, tf_id,
                    result.error.code if result.error else "UNKNOWN",
                )
        except Exception:
            logger.exception(
                "[Scheduler] Fetch ERROR — symbol=%d tf=%d", symbol_id, tf_id
            )
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Paso 3: cleanup de candles
    # ------------------------------------------------------------------
    for (symbol_id, tf_id) in fetched_pairs:
        session = SessionLocal()
        try:
            deleted = _cleanup_candles(session, symbol_id, tf_id, retention)
            if deleted:
                logger.info(
                    "[Scheduler] Cleanup candles — symbol=%d tf=%d deleted=%d",
                    symbol_id, tf_id, deleted,
                )
        except Exception:
            logger.exception(
                "[Scheduler] Cleanup candles ERROR — symbol=%d tf=%d",
                symbol_id, tf_id,
            )
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Paso 4: calculate features por tripla
    # ------------------------------------------------------------------
    for (symbol_id, tf_id, fs_id) in calc_triplets:
        if (symbol_id, tf_id) not in fetched_pairs:
            continue

        session = SessionLocal()
        try:
            result = FeatureServiceFactory(session).calculate_features().calculate(
                symbol_id=symbol_id,
                timeframe_id=tf_id,
                feature_set_id=fs_id,
            )
            if result.success:
                logger.info(
                    "[Scheduler] Features OK — symbol=%d tf=%d fs=%d rows=%d",
                    symbol_id, tf_id, fs_id,
                    result.data["rows_calculated"],
                )
            else:
                logger.warning(
                    "[Scheduler] Features FAIL — symbol=%d tf=%d fs=%d code=%s",
                    symbol_id, tf_id, fs_id,
                    result.error.code if result.error else "UNKNOWN",
                )
        except Exception:
            logger.exception(
                "[Scheduler] Features ERROR — symbol=%d tf=%d fs=%d",
                symbol_id, tf_id, fs_id,
            )
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Paso 5: cleanup de candle_features
    # ------------------------------------------------------------------
    for (symbol_id, tf_id, fs_id) in calc_triplets:
        if (symbol_id, tf_id) not in fetched_pairs:
            continue

        session = SessionLocal()
        try:
            deleted = _cleanup_candle_features(
                session, symbol_id, tf_id, fs_id, retention
            )
            if deleted:
                logger.info(
                    "[Scheduler] Cleanup features — symbol=%d tf=%d fs=%d deleted=%d",
                    symbol_id, tf_id, fs_id, deleted,
                )
        except Exception:
            logger.exception(
                "[Scheduler] Cleanup features ERROR — symbol=%d tf=%d fs=%d",
                symbol_id, tf_id, fs_id,
            )
        finally:
            session.close()
