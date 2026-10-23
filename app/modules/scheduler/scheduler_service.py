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
#      calcular features si se obtuvieron velas nuevas o si sus features
#      van detrás de la última vela (p. ej. un bot recién iniciado sobre
#      un par que ya estaba al día, o con otro conjunto de indicadores).
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
from datetime import datetime

from app.common.config import settings
from app.common.utils import utc_now
from app.extensions.db.session import SessionLocal
from app.modules.bots.infrastructure.bot_repository_impl import SqlAlchemyBotRepository
from app.modules.features.infrastructure.candle_feature_repository_impl import (
    SqlAlchemyCandleFeatureRepository,
)
from app.modules.features.providers.feature_provider import FeatureServiceFactory
from app.modules.market.infrastructure.candle_repository_impl import SqlAlchemyCandleRepository
from app.modules.market.infrastructure.timeframe_repository_impl import (
    SqlAlchemyTimeframeRepository,
)
from app.modules.market.providers.market_provider import MarketServiceFactory

logger = logging.getLogger(__name__)

# Límite de velas para carga inicial (sin datos previos)
_INITIAL_FETCH_LIMIT = 500
# Límite para actualizaciones incrementales (vela nueva + margen)
_INCREMENTAL_FETCH_LIMIT = 3


# ======================================================================
# Helpers
# ======================================================================

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

    now = utc_now()
    elapsed = (now - latest_ts).total_seconds()

    if elapsed >= timeframe_seconds:
        return True, _INCREMENTAL_FETCH_LIMIT

    return False, 0


# ======================================================================
# Explorador de tendencia
# ======================================================================

def refresh_explorer() -> None:
    """
    Trae las velas 1d que faltan para el explorador de tendencia (M2).

    Va aparte de run_cycle(): el explorador necesita datos de todos los
    símbolos, haya o no agentes activos. Sin `force`: solo descarga los
    símbolos cuya última vela diaria tiene un día o más.
    """
    session = SessionLocal()
    try:
        result = MarketServiceFactory(session).refresh_explorer_candles().refresh()
        if result.success:
            d = result.data
            logger.info(
                "[Scheduler] Explorador — actualizados=%d al día=%d fallidos=%d",
                len(d["updated"]), len(d["skipped"]), len(d["failed"]),
            )
            for item in d["failed"]:
                logger.warning(
                    "[Scheduler] Explorador FAIL — %s code=%s", item["symbol"], item["code"]
                )
        else:
            logger.warning(
                "[Scheduler] Explorador omitido — code=%s",
                result.error.code if result.error else "UNKNOWN",
            )
    except Exception:
        logger.exception("[Scheduler] Explorador ERROR")
    finally:
        session.close()


# ======================================================================
# Billetera de la plataforma
# ======================================================================

def sync_platform_wallet() -> None:
    """
    Lee el saldo de la billetera de la plataforma y guarda su foto (M4).

    Va aparte de run_cycle(): corre cada WALLET_SYNC_INTERVAL_SECONDS, haya
    o no agentes activos. Sin billetera configurada no hace nada.
    """
    # Import diferido: accounts arma clientes ccxt al construir su factory
    from app.modules.accounts.providers import AccountServiceFactory

    session = SessionLocal()
    try:
        result = AccountServiceFactory(session).sync_wallet().sync()
        if result.success:
            snapshot = result.data
            logger.info(
                "[Scheduler] Billetera — total=%s %s libre=%s sin precio=%d",
                snapshot.total_value, snapshot.base_asset, snapshot.free_value,
                len(snapshot.missing_prices),
            )
        elif result.error and result.error.code == "WALLET_NOT_CONFIGURED":
            logger.debug("[Scheduler] Billetera sin configurar. Sincronización omitida.")
        else:
            logger.warning(
                "[Scheduler] Billetera FAIL — code=%s",
                result.error.code if result.error else "UNKNOWN",
            )
    except Exception:
        logger.exception("[Scheduler] Billetera ERROR")
    finally:
        session.close()


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
       y calcula features cuando hubo fetch exitoso o cuando van atrasadas
       respecto a la última vela.
    4. Limpia candles y candle_features más allá del retention limit.
    """
    retention = settings.SCHEDULER_RETENTION_CANDLES

    # ------------------------------------------------------------------
    # Paso 1: leer bots activos y construir los conjuntos de trabajo
    # ------------------------------------------------------------------
    session = SessionLocal()
    try:
        bots = SqlAlchemyBotRepository(session).list_by_statuses(["running", "paused"])
        if not bots:
            logger.debug("[Scheduler] No hay bots activos. Ciclo omitido.")
            return

        timeframe_repo = SqlAlchemyTimeframeRepository(session)
        candle_repo = SqlAlchemyCandleRepository(session)
        feature_repo = SqlAlchemyCandleFeatureRepository(session)

        # Pares únicos para fetch: (symbol_id, timeframe_id) → seconds
        fetch_pairs: dict[tuple[int, int], int] = {}
        for bot in bots:
            key = (bot.symbol_id, bot.timeframe_id)
            if key not in fetch_pairs:
                tf = timeframe_repo.get_by_id(bot.timeframe_id)
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
        latest_candle_ts: dict[tuple[int, int], datetime | None] = {}
        for (symbol_id, tf_id), tf_seconds in fetch_pairs.items():
            latest_ts = candle_repo.get_latest_ts(symbol_id, tf_id)
            latest_candle_ts[(symbol_id, tf_id)] = latest_ts
            should, limit = _should_fetch(latest_ts, tf_seconds)
            if should:
                fetch_needed[(symbol_id, tf_id)] = limit

        # Triplas con velas pero con features atrasadas o inexistentes
        stale_triplets: set[tuple[int, int, int]] = set()
        for (symbol_id, tf_id, fs_id) in calc_triplets:
            candle_ts = latest_candle_ts.get((symbol_id, tf_id))
            if candle_ts is None:
                continue
            latest_features = feature_repo.list_features(
                symbol_id=symbol_id, timeframe_id=tf_id, feature_set_id=fs_id, limit=1
            )
            if not latest_features or latest_features[0].ts < candle_ts:
                stale_triplets.add((symbol_id, tf_id, fs_id))

    finally:
        session.close()

    if not fetch_needed and not stale_triplets:
        logger.debug("[Scheduler] Velas e indicadores vigentes. Ciclo omitido.")
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
            candle_repo = SqlAlchemyCandleRepository(session)
            deleted = candle_repo.delete_beyond_retention(symbol_id, tf_id, retention)
            candle_repo.commit()
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
    # Paso 4: calculate features por tripla (velas nuevas o atrasadas)
    # ------------------------------------------------------------------
    to_calculate = {
        t for t in calc_triplets
        if (t[0], t[1]) in fetched_pairs or t in stale_triplets
    }
    for (symbol_id, tf_id, fs_id) in to_calculate:
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
    for (symbol_id, tf_id, fs_id) in to_calculate:
        session = SessionLocal()
        try:
            feature_repo = SqlAlchemyCandleFeatureRepository(session)
            deleted = feature_repo.delete_beyond_retention(
                symbol_id, tf_id, fs_id, retention
            )
            feature_repo.commit()
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
