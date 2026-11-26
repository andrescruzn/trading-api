# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/risk/risk_gate_service.py
#
# PROPÓSITO:
# - Última barrera antes de enviar una orden al ejecutor. Aplica las
#   salvaguardas del servidor, se cree la orden a mano, desde una señal
#   aprobada por una persona o en modo automático.
#
# REGLAS (en orden):
# 1. Kill switch global: TRADING_ENABLED=false → no sale ninguna orden
#    (ni de agentes reales ni de agentes demo). No hay interruptor aparte
#    para lo real: los agentes reales y los demo conviven (2026-10-26).
# 2. Solo para órdenes que ABREN riesgo (buy en spot):
#    a. Notional máximo: qty × precio ≤ min(ORDER_MAX_NOTIONAL,
#       risk_params.max_notional).
#    b. Drawdown máximo del bot: si la pérdida realizada acumulada supera
#       max_drawdown_pct del capital, el bot pasa a `error` y no abre más
#       (queda en su historial como cambio del sistema).
#    Las ventas (cerrar o reducir) no se bloquean por estas reglas: reducir
#    riesgo siempre debe poder hacerse mientras el kill switch esté abierto.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.common.config import settings
from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_history import (
    BOT_STATUS_CHANGED,
    REASON_MAX_DRAWDOWN,
    status_change_data,
)
from app.modules.bots.domain.bot_history_repository import BotHistoryRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.domain.fund_capital_port import FundCapitalPort
from app.modules.orders.domain.position_repository import PositionRepository


class RiskGateService:
    """Valida una orden contra las salvaguardas de trading del servidor."""

    def __init__(
        self,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
        balance_repo: AccountBalanceRepository,
        position_repo: PositionRepository,
        fund_capital: FundCapitalPort | None = None,
        history_repo: BotHistoryRepository | None = None,
    ):
        self._bot_repo = bot_repo
        self._account_repo = account_repo
        self._balance_repo = balance_repo
        self._position_repo = position_repo
        self._fund_capital = fund_capital
        self._history_repo = history_repo

    def check(
        self,
        bot: Bot,
        side: str,
        qty: Decimal,
        reference_price: Decimal,
    ) -> ServiceResult[None]:
        if not settings.TRADING_ENABLED:
            return ServiceResult.fail(code="TRADING_DISABLED", http_status=503)

        if side != "buy":
            return ServiceResult.ok(data=None)

        # --------------------------------------------------------------
        # a. Notional máximo
        # --------------------------------------------------------------
        notional = qty * reference_price
        limits = [
            Decimal(str(value))
            for value in (settings.ORDER_MAX_NOTIONAL, bot.max_notional)
            if value
        ]
        if limits and notional > min(limits):
            return ServiceResult.fail(
                code="ORDER_NOTIONAL_TOO_HIGH",
                http_status=422,
                meta={"notional": str(notional), "max": str(min(limits))},
            )

        # --------------------------------------------------------------
        # b. Drawdown máximo del bot
        # --------------------------------------------------------------
        if bot.max_drawdown_pct and self._drawdown_reached(bot):
            if bot.can_transition_to("error"):
                old_status = bot.status
                bot.status = "error"
                self._bot_repo.update(bot)
                if self._history_repo is not None:
                    # Sin user_id: lo decidió el sistema
                    self._history_repo.record(
                        bot_id=bot.id,
                        event_type=BOT_STATUS_CHANGED,
                        data=status_change_data(old_status, "error", REASON_MAX_DRAWDOWN),
                    )
                self._bot_repo.commit()
            return ServiceResult.fail(
                code="BOT_MAX_DRAWDOWN_REACHED",
                http_status=409,
                meta={"max_drawdown_pct": bot.max_drawdown_pct},
            )

        return ServiceResult.ok(data=None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _drawdown_reached(self, bot: Bot) -> bool:
        """
        Pérdida realizada acumulada del bot ≥ max_drawdown_pct del capital.

        Capital = saldo libre actual en la moneda base de la cuenta + la
        pérdida ya realizada (aproxima el capital con el que empezó).

        Agente del fondo común: la caída se mide desde la equity de su última
        liquidación hasta su capital de ahora (la billetera es de todos y su
        saldo no dice nada de este agente).
        """
        fund = self._fund_capital.capital_for(bot) if self._fund_capital else None
        if fund is not None:
            if fund.settled_equity <= Decimal("0"):
                return False
            loss = fund.settled_equity - fund.capital
            return loss > 0 and loss / fund.settled_equity >= Decimal(str(bot.max_drawdown_pct))

        realized = sum(
            (p.realized_pnl for p in self._position_repo.list_by_bot(bot_id=bot.id)),
            Decimal("0"),
        )
        if realized >= Decimal("0"):
            return False

        account = self._account_repo.get_by_id(bot.account_id) if bot.account_id else None
        if account is None:
            return False
        balance = self._balance_repo.get_latest_by_asset(
            account_id=account.id,
            asset=account.base_currency,
        )
        free = Decimal(str(balance.free)) if balance is not None else Decimal("0")

        loss = -realized
        capital = free + loss
        if capital <= Decimal("0"):
            return True
        return loss / capital >= Decimal(str(bot.max_drawdown_pct))
