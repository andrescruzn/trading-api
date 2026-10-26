# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/wallet_gateway.py
#
# Contrato con el exchange de la billetera de la plataforma.
# Implementado en infrastructure/ccxt_wallet_gateway.py (ccxt).
#
# DECISIÓN:
# - Contrato aparte del exchange: hoy la billetera es siempre Binance
#   (ccxt); otro proveedor necesitaría su propia implementación.
# - Los errores salen como `WalletGatewayError(code)`: el servicio los
#   traduce a ServiceResult y la ruta a texto de UI.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.wallet_snapshot_entity import AssetBalance

# Estado de un depósito en el exchange (unificado por ccxt)
EXCHANGE_DEPOSIT_STATUSES = ("pending", "ok", "failed", "canceled")


class WalletGatewayError(Exception):
    """Fallo al hablar con el exchange; `code` es un código estable de error."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code


@dataclass(frozen=True)
class ExchangeDeposit:
    """Un depósito tal como lo reporta el exchange."""

    txid: str
    amount: Decimal
    asset: str
    network: str | None
    status: str
    address_from: str | None
    exchange_id: str | None
    ts: datetime | None


@dataclass(frozen=True)
class ExchangeWithdrawal:
    """Un retiro enviado desde la billetera, tal como lo reporta el exchange."""

    txid: str
    amount: Decimal          # lo que recibe el destino
    fee: Decimal             # comisión de red que cobró el exchange
    asset: str
    network: str | None
    address: str | None
    tag: str | None
    status: str              # pending | ok | failed | canceled
    exchange_id: str | None
    ts: datetime | None


@dataclass(frozen=True)
class WithdrawNetwork:
    """Red por la que el exchange envía un activo, con su comisión y mínimo."""

    code: str
    name: str
    withdraw_enabled: bool
    fee: Decimal | None
    min_amount: Decimal | None


@dataclass(frozen=True)
class DepositNetwork:
    """Red por la que el exchange acepta depósitos de un activo (p. ej. TRC20)."""

    code: str
    name: str
    deposit_enabled: bool


@dataclass(frozen=True)
class DepositAddress:
    """Dirección de depósito de la billetera en una red (`tag` = memo, si la red lo usa)."""

    network: str
    address: str
    tag: str | None


class WalletGateway(Protocol):

    def fetch_balances(self, account: Account) -> list[AssetBalance]:
        """Saldos reales de la cuenta (libre y en órdenes) por activo."""
        ...

    def fetch_prices(
        self, account: Account, assets: list[str], quote: str
    ) -> dict[str, Decimal]:
        """
        Último precio de cada activo en `quote` (par `ACTIVO/quote`).
        Los activos sin mercado o sin precio no vienen en el resultado.
        """
        ...

    def fetch_deposits(
        self, account: Account, asset: str, since: datetime | None
    ) -> list[ExchangeDeposit]:
        """Depósitos recibidos de `asset` desde `since` (con su txid y estado)."""
        ...

    def fetch_deposit_networks(self, account: Account, asset: str) -> list[DepositNetwork]:
        """Redes del exchange para `asset` (con si aceptan depósitos hoy)."""
        ...

    def fetch_deposit_address(
        self, account: Account, asset: str, network: str
    ) -> DepositAddress:
        """Dirección de depósito de la cuenta en esa red."""
        ...

    def fetch_withdraw_networks(self, account: Account, asset: str) -> list[WithdrawNetwork]:
        """Redes por las que se puede enviar `asset`, con comisión y mínimo."""
        ...

    def fetch_withdrawals(
        self, account: Account, asset: str, since: datetime | None
    ) -> list[ExchangeWithdrawal]:
        """Retiros enviados de `asset` desde `since` (solo lectura del historial)."""
        ...
