# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/scheduler/execution_cycle.py
#
# PROPÓSITO:
# - Ciclo de ejecución de los agentes, después de velas e indicadores
#   (run_cycle). Solo lo corre el proceso líder (SchedulerLock):
#   1. Señales automáticas: agentes `running` en modo approval/auto con
#      una vela CERRADA nueva → una señal por vela (candle_ts).
#      - approval → queda pendiente y se avisa por Telegram.
#      - auto     → se ejecuta en el acto (ExecuteSignalService).
#   2. Caducar las señales pendientes vencidas.
#   3. Proteger posiciones: cerrar las que tocaron su SL/TP.
#   4. Telegram en modo polling (desarrollo): procesar mensajes y botones.
#
# SALVAGUARDAS:
# - Timeframe mínimo (SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS) y tope diario de
#   análisis por usuario (AGENT_MAX_AUTO_ANALYSES_PER_DAY): coste de IA.
# - No se analiza una vela vieja: si la última cerrada tiene más de dos
#   timeframes de antigüedad (descarga caída), se omite el agente.
# - Una sesión por agente y errores aislados: un agente no frena a otros.
# ======================================================================

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.common.config import settings
from app.common.utils import utc_now
from app.extensions.db.session import SessionLocal
from app.modules.accounts.infrastructure import SqlAlchemyAccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.infrastructure import SqlAlchemyBotRepository, SqlAlchemySignalRepository
from app.modules.features.infrastructure.candle_feature_repository_impl import (
    SqlAlchemyCandleFeatureRepository,
)
from app.modules.market.infrastructure.candle_repository_impl import SqlAlchemyCandleRepository
from app.modules.market.infrastructure.timeframe_repository_impl import (
    SqlAlchemyTimeframeRepository,
)

logger = logging.getLogger(__name__)


def run_execution_cycle() -> None:
    """Pasos de ejecución, cada uno aislado: si uno falla, los demás corren."""
    for step in (_generate_automatic_signals, _expire_pending_signals, _protect_positions, _poll_telegram):
        try:
            step()
        except Exception:
            logger.exception("[Execution] Error no controlado en %s", step.__name__)


# ======================================================================
# 1. Señales automáticas
# ======================================================================

def _generate_automatic_signals() -> None:
    session = SessionLocal()
    try:
        bots = [
            bot
            for bot in SqlAlchemyBotRepository(session).list_by_statuses(["running"])
            if bot.is_automated() and bot.feature_set_id is not None and bot.account_id is not None
        ]
    finally:
        session.close()

    if not bots:
        return

    day_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    analyses_today: dict[int, int] = {}

    for bot in bots:
        session = SessionLocal()
        try:
            candle_ts = _closed_candle_to_analyze(session, bot)
            if candle_ts is None:
                continue

            owner_id = SqlAlchemyAccountRepository(session).get_by_id(bot.account_id).user_id
            if owner_id not in analyses_today:
                analyses_today[owner_id] = _count_owner_signals_since(session, owner_id, day_start)
            if analyses_today[owner_id] >= settings.AGENT_MAX_AUTO_ANALYSES_PER_DAY:
                logger.info(
                    "[Execution] Tope diario de análisis alcanzado — user=%d bot=%d",
                    owner_id, bot.id,
                )
                continue

            _generate_for_bot(session, bot, candle_ts)
            analyses_today[owner_id] += 1
        except Exception:
            session.rollback()
            logger.exception("[Execution] Señal automática ERROR — bot=%d", bot.id)
        finally:
            session.close()


def _closed_candle_to_analyze(session, bot: Bot) -> datetime | None:
    """ts de la última vela cerrada con indicadores y sin señal; None si no toca."""
    timeframe = SqlAlchemyTimeframeRepository(session).get_by_id(bot.timeframe_id)
    if timeframe is None or timeframe.seconds < settings.SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS:
        return None

    now = utc_now()
    period = timedelta(seconds=timeframe.seconds)

    # Vela cerrada = abrió hace al menos un timeframe completo
    candles = SqlAlchemyCandleRepository(session).list_candles(
        symbol_id=bot.symbol_id,
        timeframe_id=bot.timeframe_id,
        to_ts=now - period,
        limit=1,
    )
    if not candles:
        return None
    candle_ts = candles[0].ts
    if candle_ts.tzinfo is None:
        candle_ts = candle_ts.replace(tzinfo=now.tzinfo)

    # Datos viejos (descarga caída): no decidir con una vela de hace horas
    if now - candle_ts > 2 * period:
        return None

    features = SqlAlchemyCandleFeatureRepository(session).list_features(
        symbol_id=bot.symbol_id,
        timeframe_id=bot.timeframe_id,
        feature_set_id=bot.feature_set_id,
        to_ts=candle_ts,
        limit=1,
    )
    if not features or features[0].ts.replace(tzinfo=None) != candle_ts.replace(tzinfo=None):
        return None  # indicadores aún no calculados para esa vela

    if SqlAlchemySignalRepository(session).exists_for_candle(bot.id, candle_ts):
        return None

    return candle_ts


def _count_owner_signals_since(session, owner_id: int, since: datetime) -> int:
    account_ids = [a.id for a in SqlAlchemyAccountRepository(session).list_by_user_id(owner_id)]
    bot_ids = [b.id for b in SqlAlchemyBotRepository(session).list_by_account_ids(account_ids)]
    return SqlAlchemySignalRepository(session).count_created_since(bot_ids, since)


def _generate_for_bot(session, bot: Bot, candle_ts: datetime) -> None:
    from app.modules.bots.providers import BotServiceFactory
    from app.modules.orders.providers import OrderServiceFactory

    try:
        result = BotServiceFactory(session=session).generate_signal().generate(
            bot.id, owner_id=None, candle_ts=candle_ts
        )
    except IntegrityError:
        # Otra ejecución ya creó la señal de esta vela (UNIQUE bot_id, candle_ts)
        session.rollback()
        return

    if not result.success:
        logger.warning(
            "[Execution] Señal automática FAIL — bot=%d code=%s", bot.id, result.error.code
        )
        return

    signal = result.data
    logger.info(
        "[Execution] Señal automática — bot=%d action=%s decision=%s",
        bot.id, signal.action, signal.decision_status,
    )

    if signal.is_pending() and bot.execution_mode == "auto":
        executed = OrderServiceFactory(session=session).execute_signal().execute(
            signal.id, owner_id=None, decided_by_user_id=None, channel="auto"
        )
        if executed.success:
            logger.info("[Execution] Orden automática — bot=%d signal=%d", bot.id, signal.id)
        else:
            logger.warning(
                "[Execution] Orden automática FAIL — bot=%d signal=%d code=%s",
                bot.id, signal.id, executed.error.code,
            )


# ======================================================================
# 2. Caducar pendientes
# ======================================================================

def _expire_pending_signals() -> None:
    session = SessionLocal()
    try:
        repo = SqlAlchemySignalRepository(session)
        expired = repo.expire_pending(utc_now())
        repo.commit()
        if expired:
            logger.info("[Execution] Señales vencidas: %d", len(expired))
    finally:
        session.close()


# ======================================================================
# 3. Stop loss / take profit
# ======================================================================

def _protect_positions() -> None:
    from app.modules.orders.providers import OrderServiceFactory

    session = SessionLocal()
    try:
        report = OrderServiceFactory(session=session).protect_positions().run().data
        if report.closed or report.failed:
            logger.info(
                "[Execution] Protección SL/TP — revisadas=%d cerradas=%d fallidas=%d",
                report.checked, len(report.closed), len(report.failed),
            )
    finally:
        session.close()


# ======================================================================
# 4. Telegram (polling en desarrollo)
# ======================================================================

def _poll_telegram() -> None:
    if settings.TELEGRAM_UPDATES_MODE != "polling" or not settings.TELEGRAM_BOT_TOKEN:
        return

    from app.modules.alerts.channels.telegram_poller import fetch_updates
    from app.modules.alerts.providers.telegram_provider import build_telegram_update_service

    for update in fetch_updates(settings.TELEGRAM_BOT_TOKEN):
        session = SessionLocal()
        try:
            service = build_telegram_update_service(session)
            if service is not None:
                service.handle(update)
        except Exception:
            session.rollback()
            logger.exception("[Execution] Telegram update ERROR — id=%s", update.get("update_id"))
        finally:
            session.close()
