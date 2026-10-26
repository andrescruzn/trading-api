# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/pools/agent_capital_service.py
#
# PROPÓSITO:
# - Implementa FundCapitalPort (dominio de bots): con cuánto dinero opera un
#   agente del fondo común. Lo usan la regla del 1 % (señales) y el
#   drawdown del RiskGate (M8).
#
# REGLAS:
# - Agente con pool: capital = equity de la última liquidación + flujo de
#   caja desde entonces (con el funding de los perpetuos) + lo abierto a
#   precio de costo (qty × precio medio). Con 1x, el costo de un perpetuo es
#   su margen.
#   Es la equity "a costo": no depende del precio del momento.
# - Agente sobre la billetera de la plataforma sin pool: capital 0 (no puede
#   arriesgar el dinero de todos por fuera del fondo).
# - Cualquier otro agente: None (usa el saldo libre de su cuenta).
# ======================================================================

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from app.modules.accounts.domain.platform_wallet_repository import PlatformWalletRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.fund_capital_port import FundCapital
from app.modules.fund.domain.agent_pool_entity import AgentPool
from app.modules.fund.domain.fund_repositories import AgentPoolRepository
from app.modules.fund.domain.settlement import CashFlow, cash_flow
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.funding_repository import FundingRepository
from app.modules.orders.domain.position_repository import PositionRepository

_ZERO = Decimal("0")


class AgentCapitalService:

    def __init__(
        self,
        *,
        pool_repo: AgentPoolRepository,
        wallet_repo: PlatformWalletRepository,
        fill_repo: FillRepository,
        position_repo: PositionRepository,
        symbol_repo: SymbolRepository,
        funding_repo: FundingRepository,
    ):
        self._funding_repo = funding_repo
        self._pool_repo = pool_repo
        self._wallet_repo = wallet_repo
        self._fill_repo = fill_repo
        self._position_repo = position_repo
        self._symbol_repo = symbol_repo

    # ------------------------------------------------------------------
    # FundCapitalPort
    # ------------------------------------------------------------------

    def capital_for(self, bot: Bot) -> FundCapital | None:
        pool = self._pool_repo.get_by_bot(bot.id)
        if pool is None:
            wallet = self._wallet_repo.get()
            if wallet is not None and bot.account_id == wallet.account_id:
                return FundCapital(capital=_ZERO, settled_equity=_ZERO)
            return None

        flow = self.flow_since_settlement(pool, bot)
        capital = pool.equity + flow.net + self.open_cost(bot.id)
        return FundCapital(capital=max(capital, _ZERO), settled_equity=pool.equity)

    # ------------------------------------------------------------------
    # Piezas reutilizadas por la liquidación
    # ------------------------------------------------------------------

    def flow_since_settlement(self, pool: AgentPool, bot: Bot) -> CashFlow:
        """Flujo de caja de los fills y el funding del bot que aún no entraron a una liquidación."""
        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        flow = cash_flow(
            self._fill_repo.list_by_bot_after(bot.id, pool.last_fill_id),
            quote=pool.asset,
            base=symbol.base_asset if symbol else None,
            after_fill_id=pool.last_fill_id,
        )
        funding, last_funding_id = self._funding_repo.total_after(bot.id, pool.last_funding_id)
        return replace(flow, funding=funding, last_funding_id=last_funding_id)

    def funding_start(self, bot_id: int) -> int:
        """Último funding del bot hoy: lo anterior a abrirlo al fondo no cuenta."""
        return self._funding_repo.total_after(bot_id, 0)[1]

    def open_cost(self, bot_id: int) -> Decimal:
        """Lo que hay en posiciones abiertas, a precio de costo."""
        return sum(
            (
                p.qty * p.avg_price
                for p in self._position_repo.list_by_bot(bot_id=bot_id)
                if p.qty > 0
            ),
            _ZERO,
        )
