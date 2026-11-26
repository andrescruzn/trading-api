# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/wallet_snapshot_entity.py
#
# Entidad de dominio: WalletSnapshot.
# Foto del saldo de la billetera de la plataforma, valorado en la moneda
# base (USDT), con el desglose por activo. Las fotos son inmutables: la
# serie temporal es la historia del saldo total.
#
# Incluye la valoración pura (`value_wallet`): balances + precios → foto.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

# Orígenes de una foto: leída del exchange o armada con balances manuales
WALLET_SNAPSHOT_SOURCES = ("exchange", "manual")


@dataclass(frozen=True)
class AssetBalance:
    """Saldo de un activo en la billetera (libre + en órdenes)."""

    asset: str
    free: Decimal
    locked: Decimal

    @property
    def total(self) -> Decimal:
        return self.free + self.locked


@dataclass(frozen=True)
class WalletAssetLine:
    """Un activo de la foto con su precio en la moneda base (None = sin precio)."""

    asset: str
    free: Decimal
    locked: Decimal
    price: Decimal | None
    value: Decimal | None

    @property
    def total(self) -> Decimal:
        return self.free + self.locked


@dataclass
class WalletSnapshot:
    """
    Foto valorada de la billetera.

    Reglas de negocio:
    - total_value = free_value + locked_value, en `base_asset`.
    - Un activo sin precio no suma al total: queda en `missing_prices` para
      que los propietarios sepan que el total está incompleto.
    """

    id: int
    account_id: int
    base_asset: str
    total_value: Decimal
    free_value: Decimal
    locked_value: Decimal
    source: str
    assets: list[WalletAssetLine] = field(default_factory=list)
    missing_prices: list[str] = field(default_factory=list)
    ts: datetime | None = None


def value_wallet(
    *,
    account_id: int,
    base_asset: str,
    balances: list[AssetBalance],
    prices: dict[str, Decimal],
    source: str,
    ts: datetime | None = None,
) -> WalletSnapshot:
    """
    Valora los balances en la moneda base.

    - La moneda base vale 1.
    - Los activos con saldo 0 no entran en la foto.
    - `prices` trae el precio de cada activo en la moneda base; si falta,
      el activo se lista pero no suma.
    """
    base = base_asset.upper()
    lines: list[WalletAssetLine] = []
    missing: list[str] = []
    free_value = Decimal("0")
    locked_value = Decimal("0")

    for balance in sorted(balances, key=lambda b: b.asset):
        if balance.total <= 0:
            continue
        asset = balance.asset.upper()
        price = Decimal("1") if asset == base else prices.get(asset)
        if price is None:
            missing.append(asset)
            lines.append(WalletAssetLine(asset, balance.free, balance.locked, None, None))
            continue
        free_value += balance.free * price
        locked_value += balance.locked * price
        lines.append(
            WalletAssetLine(asset, balance.free, balance.locked, price, balance.total * price)
        )

    return WalletSnapshot(
        id=0,
        account_id=account_id,
        base_asset=base,
        total_value=free_value + locked_value,
        free_value=free_value,
        locked_value=locked_value,
        source=source,
        assets=lines,
        missing_prices=missing,
        ts=ts,
    )
