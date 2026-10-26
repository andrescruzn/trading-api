# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/ccxt_wallet_gateway.py
#
# Implementación ccxt de WalletGateway: saldo y precios de la billetera,
# depósitos, redes y direcciones para verificar lo que entra al fondo, y el
# historial de retiros para verificar lo que sale.
#
# DECISIONES:
# - El saldo de un exchange puede estar repartido en varias "cuentas"
#   internas. En Binance el P2P y los depósitos suelen caer en Funding, no
#   en Spot: si no se suman, la conciliación del fondo daría diferencias.
#   `_EXTRA_BALANCE_TYPES` lista los tipos adicionales que se suman a
#   `fetch_balance()` por exchange. Desde el 2026-10-26 también Futuros
#   USDⓈ-M (`future`): el margen de los perpetuos en live vive ahí.
# - Un tipo adicional que falle (p. ej. permiso de la API key) no tumba la
#   sincronización: se registra en el log y se suma lo que sí se leyó.
#   Si falla el saldo principal, sí es error.
# - Precios: `fetch_tickers` del par `ACTIVO/quote` (último precio), con
#   datos públicos; no hace falta API key.
# ======================================================================

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import ccxt

from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.wallet_gateway import (
    DepositAddress,
    DepositNetwork,
    ExchangeDeposit,
    ExchangeWithdrawal,
    WalletGatewayError,
    WithdrawNetwork,
)
from app.modules.accounts.domain.wallet_snapshot_entity import AssetBalance
from app.modules.accounts.infrastructure.exchange_client import (
    ExchangeClientError,
    build_authenticated_client,
    build_public_client,
)
from app.modules.market.domain.exchange_repository import ExchangeRepository

logger = logging.getLogger(__name__)

# Tipos de cuenta que se suman al saldo principal (id ccxt → `type` de fetch_balance)
_EXTRA_BALANCE_TYPES: dict[str, tuple[str, ...]] = {
    "binance": ("funding", "future"),
}

# Códigos de ExchangeClientError → código de la billetera
_CLIENT_ERROR_CODES: dict[str, str] = {
    "ACCOUNT_NO_EXCHANGE": "WALLET_ACCOUNT_NO_EXCHANGE",
    "EXCHANGE_NOT_FOUND": "WALLET_ACCOUNT_NO_EXCHANGE",
    "EXCHANGE_NOT_SUPPORTED": "WALLET_EXCHANGE_NOT_SUPPORTED",
    "ACCOUNT_NO_CREDENTIALS": "WALLET_ACCOUNT_NO_CREDENTIALS",
    "ACCOUNT_CREDENTIALS_INCOMPLETE": "WALLET_ACCOUNT_NO_CREDENTIALS",
    "ACCOUNT_CREDENTIALS_UNREADABLE": "WALLET_CREDENTIALS_UNREADABLE",
}


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _to_decimal_or_none(value: Any) -> Decimal | None:
    return None if value is None else _to_decimal(value)


def _unified_network(client: Any, network: str | None, asset: str) -> str | None:
    """
    El historial trae el id de red de Binance (`TRX`, `BSC`); las redes de
    `fetch_currencies` vienen con el código unificado de ccxt (`TRC20`,
    `BEP20`). Se traduce para poder compararlas.
    """
    if not network:
        return None
    try:
        return client.network_id_to_code(network, asset.upper()) or network
    except Exception:
        return network


def _translate_ccxt_error(exc: Exception) -> WalletGatewayError:
    if isinstance(exc, (ccxt.AuthenticationError, ccxt.PermissionDenied)):
        return WalletGatewayError("WALLET_EXCHANGE_AUTH_FAILED", str(exc))
    if isinstance(exc, (ccxt.NetworkError, ccxt.ExchangeNotAvailable)):
        return WalletGatewayError("WALLET_EXCHANGE_UNAVAILABLE", str(exc))
    return WalletGatewayError("WALLET_SYNC_FAILED", str(exc))


class CcxtWalletGateway:
    """WalletGateway sobre ccxt para los exchanges de CCXT_EXCHANGE_MAP."""

    def __init__(self, exchange_repo: ExchangeRepository, cipher: CredentialsCipher):
        self._exchange_repo = exchange_repo
        self._cipher = cipher

    # ==================================================================
    # Saldo
    # ==================================================================

    def fetch_balances(self, account: Account) -> list[AssetBalance]:
        client = self._client(account, authenticated=True)
        free: dict[str, Decimal] = defaultdict(Decimal)
        locked: dict[str, Decimal] = defaultdict(Decimal)

        try:
            self._accumulate(client.fetch_balance(), free, locked)
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        for balance_type in _EXTRA_BALANCE_TYPES.get(client.id, ()):
            try:
                self._accumulate(client.fetch_balance({"type": balance_type}), free, locked)
            except ccxt.BaseError as exc:
                logger.warning(
                    "[Wallet] No se pudo leer el saldo '%s' de %s (cuenta %s): %s",
                    balance_type, client.id, account.id, type(exc).__name__,
                )

        assets = set(free) | set(locked)
        return [AssetBalance(a, free[a], locked[a]) for a in sorted(assets)]

    @staticmethod
    def _accumulate(
        raw: dict[str, Any], free: dict[str, Decimal], locked: dict[str, Decimal]
    ) -> None:
        # ccxt: raw["free"] / raw["used"] = {activo: cantidad}
        for asset, amount in (raw.get("free") or {}).items():
            free[asset.upper()] += _to_decimal(amount)
        for asset, amount in (raw.get("used") or {}).items():
            locked[asset.upper()] += _to_decimal(amount)

    # ==================================================================
    # Precios
    # ==================================================================

    def fetch_prices(
        self, account: Account, assets: list[str], quote: str
    ) -> dict[str, Decimal]:
        if not assets:
            return {}
        client = self._client(account, authenticated=False)
        try:
            markets = client.load_markets()
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        pairs = {f"{asset}/{quote}": asset for asset in assets if f"{asset}/{quote}" in markets}
        if not pairs:
            return {}
        try:
            tickers = client.fetch_tickers(list(pairs))
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        prices: dict[str, Decimal] = {}
        for pair, asset in pairs.items():
            ticker = tickers.get(pair) or {}
            price = _to_decimal(ticker.get("last") or ticker.get("close"))
            if price > 0:
                prices[asset] = price
        return prices

    # ==================================================================
    # Depósitos (verificación del fondo común)
    # ==================================================================

    def fetch_deposits(
        self, account: Account, asset: str, since: datetime | None
    ) -> list[ExchangeDeposit]:
        client = self._client(account, authenticated=True)
        since_ms = int(since.timestamp() * 1000) if since else None
        try:
            raw = client.fetch_deposits(asset, since_ms)
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        deposits: list[ExchangeDeposit] = []
        for item in raw or []:
            txid = (item.get("txid") or "").strip()
            if not txid:
                # Sin txid no se puede emparejar con una solicitud
                continue
            ts_ms = item.get("timestamp")
            deposits.append(
                ExchangeDeposit(
                    txid=txid,
                    amount=_to_decimal(item.get("amount")),
                    asset=(item.get("currency") or asset).upper(),
                    network=item.get("network"),
                    status=(item.get("status") or "pending").lower(),
                    address_from=item.get("addressFrom"),
                    exchange_id=str(item["id"]) if item.get("id") is not None else None,
                    ts=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) if ts_ms else None,
                )
            )
        return deposits

    def fetch_deposit_networks(self, account: Account, asset: str) -> list[DepositNetwork]:
        client = self._client(account, authenticated=True)
        try:
            # Las redes por moneda solo vienen con credenciales en varios exchanges
            currencies = client.fetch_currencies() or {}
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        networks = (currencies.get(asset.upper()) or {}).get("networks") or {}
        return [
            DepositNetwork(
                code=str(code),
                name=str(info.get("name") or info.get("network") or code),
                deposit_enabled=info.get("deposit") is not False and info.get("active") is not False,
            )
            for code, info in sorted(networks.items())
        ]

    def fetch_deposit_address(
        self, account: Account, asset: str, network: str
    ) -> DepositAddress:
        client = self._client(account, authenticated=True)
        try:
            raw = client.fetch_deposit_address(asset.upper(), {"network": network})
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        address = (raw.get("address") or "").strip()
        if not address:
            raise WalletGatewayError("WALLET_NO_DEPOSIT_ADDRESS", f"{asset} {network}")
        return DepositAddress(
            network=network, address=address, tag=(raw.get("tag") or None)
        )

    # ==================================================================
    # Retiros (pagos del fondo común). Solo se LEE el historial: los envía
    # un super admin desde Binance y la API key no necesita permiso de retiro.
    # ==================================================================

    def fetch_withdraw_networks(self, account: Account, asset: str) -> list[WithdrawNetwork]:
        client = self._client(account, authenticated=True)
        try:
            currencies = client.fetch_currencies() or {}
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        networks = (currencies.get(asset.upper()) or {}).get("networks") or {}
        result: list[WithdrawNetwork] = []
        for code, info in sorted(networks.items()):
            limits = (info.get("limits") or {}).get("withdraw") or {}
            result.append(
                WithdrawNetwork(
                    code=str(code),
                    name=str(info.get("name") or info.get("network") or code),
                    withdraw_enabled=info.get("withdraw") is not False and info.get("active") is not False,
                    fee=_to_decimal_or_none(info.get("fee")),
                    min_amount=_to_decimal_or_none(limits.get("min")),
                )
            )
        return result

    def fetch_withdrawals(
        self, account: Account, asset: str, since: datetime | None
    ) -> list[ExchangeWithdrawal]:
        client = self._client(account, authenticated=True)
        since_ms = int(since.timestamp() * 1000) if since else None
        try:
            raw = client.fetch_withdrawals(asset, since_ms)
        except ccxt.BaseError as exc:
            raise _translate_ccxt_error(exc) from exc

        withdrawals: list[ExchangeWithdrawal] = []
        for item in raw or []:
            txid = (item.get("txid") or "").strip()
            if not txid:
                continue
            ts_ms = item.get("timestamp")
            fee = item.get("fee") or {}
            withdrawals.append(
                ExchangeWithdrawal(
                    txid=txid,
                    amount=_to_decimal(item.get("amount")),
                    fee=_to_decimal(fee.get("cost")),
                    asset=(item.get("currency") or asset).upper(),
                    network=_unified_network(client, item.get("network"), asset),
                    address=item.get("addressTo") or item.get("address"),
                    tag=item.get("tagTo") or item.get("tag"),
                    status=(item.get("status") or "pending").lower(),
                    exchange_id=str(item["id"]) if item.get("id") is not None else None,
                    ts=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) if ts_ms else None,
                )
            )
        return withdrawals

    # ==================================================================
    # Cliente
    # ==================================================================

    def _client(self, account: Account, *, authenticated: bool):
        try:
            if authenticated:
                return build_authenticated_client(account, self._exchange_repo, self._cipher)
            return build_public_client(account, self._exchange_repo)
        except ExchangeClientError as exc:
            raise WalletGatewayError(
                _CLIENT_ERROR_CODES.get(exc.code, "WALLET_SYNC_FAILED"), str(exc)
            ) from exc
