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
# 1. Kill switch global: TRADING_ENABLED=false → no sale ninguna orden.
# 2. Live apagado: TRADING_LIVE_ENABLED=false → solo paper.
# 3. Solo para órdenes que ABREN riesgo (buy en spot):
#    a. Notional máximo: qty × precio ≤ min(ORDER_MAX_NOTIONAL,
#       risk_params.max_notional).
#    b. Drawdown máximo del bot: si la pérdida realizada acumulada supera
#       max_drawdown_pct del capital, el bot pasa a `error` y no abre más.
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
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.orders.domain.position_repository import PositionRepository


class RiskGateService:
    """Valida una orden contra las salvaguardas de trading del servidor."""

    def __init__(
        self,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
        balance_repo: AccountBalanceRepository,
        position_repo: PositionRepository,
    ):
        self._bot_repo = bot_repo
        self._account_repo = account_repo
        self._balance_repo = balance_repo
        self._position_repo = position_repo

    def check(
        self,
        bot: Bot,
        side: str,
        qty: Decimal,
        reference_price: Decimal,
    ) -> ServiceResult[None]:
        if not settings.TRADING_ENABLED:
            return ServiceResult.fail(code="TRADING_DISABLED", http_status=503)

        if bot.mode == "live" and not settings.TRADING_LIVE_ENABLED:
            return ServiceResult.fail(code="TRADING_LIVE_DISABLED", http_status=403)

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
                bot.status = "error"
                self._bot_repo.update(bot)
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
        """
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
