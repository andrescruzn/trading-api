# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/execution/sync_funding_service.py
#
# PROPÓSITO:
# - Guardar el funding que Binance cobra o paga sobre las posiciones de
#   perpetuos en live (lo llama el scheduler cada FUNDING_SYNC_INTERVAL).
#   No es un fill, pero mueve dinero: entra al resultado del agente y al
#   flujo de caja del fondo común (M11).
#
# REGLAS:
# - Solo agentes live sobre un perpetuo, en cualquier estado: un agente
#   detenido puede seguir con la posición abierta.
# - Todo el funding de la cuenta en ese símbolo es del agente: hay uno solo
#   por cuenta y perpetuo (regla de M7).
# - Se pide desde el último guardado (o desde la creación del agente, con
#   un tope de 30 días); el UNIQUE (cuenta, id del exchange) evita duplicar
#   lo que se vuelva a leer.
# - Errores aislados por agente: uno que falla no frena a los demás.
# ======================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.common.utils.datetime_utils import ensure_aware_utc
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.market.domain.ccxt_exchanges import is_perpetual
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.orders.domain.funding_entity import FundingPayment
from app.modules.orders.domain.funding_repository import FundingRepository
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.execution.live_executor import LiveExecutor

logger = logging.getLogger(__name__)

_MAX_LOOKBACK = timedelta(days=30)


@dataclass
class FundingSyncReport:
    checked: int = 0
    added: int = 0
    failed: list[dict] = field(default_factory=list)


class SyncFundingService:

    def __init__(
        self,
        *,
        funding_repo: FundingRepository,
        bot_repo: BotRepository,
        symbol_repo: SymbolRepository,
        live_executor: LiveExecutor,
    ):
        self._funding_repo = funding_repo
        self._bot_repo = bot_repo
        self._symbol_repo = symbol_repo
        self._live = live_executor

    def run(self) -> ServiceResult[FundingSyncReport]:
        report = FundingSyncReport()
        bots = self._bot_repo.list_by_statuses(["running", "paused", "stopped", "error"])
        for bot in bots:
            if bot.mode != "live" or bot.account_id is None:
                continue
            symbol = self._symbol_repo.get_by_id(bot.symbol_id)
            if symbol is None or not is_perpetual(symbol.symbol):
                continue
            report.checked += 1
            try:
                report.added += self._sync_bot(bot, symbol)
                self._funding_repo.commit()
            except (RuntimeError, ExecutionUncertainError) as exc:
                self._funding_repo.rollback()
                logger.warning("[Funding] Agente %s: %s", bot.id, exc)
                report.failed.append({"bot_id": bot.id, "error": str(exc)})
        return ServiceResult.ok(report)

    def _sync_bot(self, bot, symbol) -> int:
        now = utc_now()
        last = self._funding_repo.latest_ts(bot.id)
        created = ensure_aware_utc(bot.created_at) or now - _MAX_LOOKBACK
        since = last or max(created, now - _MAX_LOOKBACK)
        rows = self._live.fetch_funding(bot, symbol.symbol, int(since.timestamp() * 1000))
        payments: list[FundingPayment] = []
        for row in rows:
            exchange_id = row.get("id")
            ts_ms = row.get("timestamp")
            if exchange_id is None or ts_ms is None:
                continue
            try:
                amount = Decimal(str(row.get("amount")))
            except (InvalidOperation, ValueError):
                continue
            if amount == 0:
                continue
            payments.append(
                FundingPayment(
                    id=0,
                    bot_id=bot.id,
                    account_id=int(bot.account_id),
                    symbol_id=symbol.id,
                    amount=amount,
                    asset=(row.get("code") or symbol.quote_asset or "USDT").upper(),
                    exchange_funding_id=str(exchange_id),
                    ts=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                )
            )
        return self._funding_repo.add_new(payments)
