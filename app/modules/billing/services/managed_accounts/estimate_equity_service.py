# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/managed_accounts/estimate_equity_service.py
#
# CASO DE USO:
# - Proponer el equity de una cuenta gestionada (para abrir o cerrar un
#   período) a partir de sus balances: el último registro de cada activo
#   (free + locked), valorado en la moneda base de la cuenta.
#
# REGLAS:
# - La moneda base vale 1. Otro activo se valora con el último cierre del
#   par `<activo>/<moneda base>` (primero en el exchange de la cuenta y,
#   si no, en cualquiera), en el timeframe más corto que tenga velas.
# - Un activo sin precio no se inventa: va en `missing` y no suma. Es una
#   sugerencia: el admin la puede corregir al cerrar.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_balance_repository import AccountBalanceRepository
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.billing.domain.managed_account_repository import ManagedAccountRepository
from app.modules.market.domain.candle_repository import CandleRepository
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.domain.timeframe_repository import TimeframeRepository

# Registros de balance a mirar: alcanza para el último de cada activo
_BALANCE_ROWS = 500


@dataclass
class EquityLine:
    asset: str
    qty: Decimal
    price: Decimal | None
    value: Decimal | None


@dataclass
class EquityEstimate:
    currency: str
    equity: Decimal
    as_of: datetime | None
    lines: list[EquityLine] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


class EstimateEquityService:
    """Equity sugerido de una cuenta gestionada desde sus balances."""

    def __init__(
        self,
        managed_account_repo: ManagedAccountRepository,
        account_repo: AccountRepository,
        balance_repo: AccountBalanceRepository,
        symbol_repo: SymbolRepository,
        timeframe_repo: TimeframeRepository,
        candle_repo: CandleRepository,
    ):
        self._managed_account_repo = managed_account_repo
        self._account_repo = account_repo
        self._balance_repo = balance_repo
        self._symbol_repo = symbol_repo
        self._timeframe_repo = timeframe_repo
        self._candle_repo = candle_repo

    def execute(self, managed_account_id: int) -> ServiceResult[EquityEstimate]:
        managed = self._managed_account_repo.find_by_id(managed_account_id)
        if managed is None:
            return ServiceResult.fail(code="BILLING_MANAGED_ACCOUNT_NOT_FOUND", http_status=404)

        account = self._account_repo.get_by_id(managed.account_id)
        if account is None:
            return ServiceResult.fail(code="BILLING_ACCOUNT_NOT_FOUND", http_status=404)
        currency = account.base_currency.upper()

        # Último registro de cada activo (la lista viene de la más reciente)
        latest = {}
        for balance in self._balance_repo.list_by_account(account.id, limit=_BALANCE_ROWS):
            latest.setdefault(balance.asset.upper(), balance)

        estimate = EquityEstimate(currency=currency, equity=Decimal("0"), as_of=None)
        for asset, balance in sorted(latest.items()):
            qty = (balance.free or Decimal("0")) + (balance.locked or Decimal("0"))
            if qty <= Decimal("0"):
                continue
            if estimate.as_of is None or (balance.ts and balance.ts > estimate.as_of):
                estimate.as_of = balance.ts
            price = Decimal("1") if asset == currency else self._last_price(
                asset, currency, account.exchange_id
            )
            value = qty * price if price is not None else None
            estimate.lines.append(EquityLine(asset=asset, qty=qty, price=price, value=value))
            if value is None:
                estimate.missing.append(asset)
            else:
                estimate.equity += value

        return ServiceResult.ok(data=estimate)

    def _last_price(self, asset: str, currency: str, exchange_id: int | None) -> Decimal | None:
        pairs = [
            s for s in self._symbol_repo.list_all()
            if (s.base_asset or "").upper() == asset and (s.quote_asset or "").upper() == currency
        ]
        pairs.sort(key=lambda s: s.exchange_id != exchange_id)
        timeframes = sorted(self._timeframe_repo.list_all(), key=lambda t: t.seconds)
        for symbol in pairs:
            for timeframe in timeframes:
                candles = self._candle_repo.list_candles(
                    symbol_id=symbol.id, timeframe_id=timeframe.id, limit=1
                )
                if candles:
                    return Decimal(str(candles[0].close))
        return None
