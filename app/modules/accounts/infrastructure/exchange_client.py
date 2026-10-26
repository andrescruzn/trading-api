# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/exchange_client.py
#
# PROPÓSITO:
# - Armar el cliente ccxt de la billetera de la plataforma: con las
#   credenciales de Binance (órdenes live de M8, saldo de la billetera,
#   depósitos y retiros del fondo) o sin ellas (precios públicos). Un solo
#   sitio para leer las credenciales y respetar LIVE_USE_SANDBOX.
#
# CREDENCIALES:
# - Hay una sola billetera (Binance) y sus credenciales viven en el `.env`
#   del servidor (BINANCE_API_KEY / BINANCE_API_SECRET), nunca en la BD.
#
# ERRORES:
# - `ExchangeClientError(code, mensaje)` hereda de RuntimeError: el
#   LiveExecutor lo trata como antes (mensaje en la orden) y la billetera
#   usa el `code` para el texto de UI.
# ======================================================================

from __future__ import annotations

from typing import Any

import ccxt

from app.common.config import settings
from app.modules.accounts.domain.account_entity import Account
from app.modules.market.domain.ccxt_exchanges import PLATFORM_EXCHANGE_NAME, ccxt_id_for
from app.modules.market.domain.exchange_repository import ExchangeRepository


class ExchangeClientError(RuntimeError):
    """No se pudo armar el cliente del exchange; `code` es estable para la UI."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def resolve_ccxt_id(account: Account, exchange_repo: ExchangeRepository) -> str:
    """Id ccxt del exchange de la cuenta (o ExchangeClientError)."""
    if account.exchange_id is None:
        raise ExchangeClientError(
            "ACCOUNT_NO_EXCHANGE",
            "La cuenta no tiene un exchange asociado.",
        )

    exchange_entity = exchange_repo.get_by_id(account.exchange_id)
    if exchange_entity is None:
        raise ExchangeClientError(
            "EXCHANGE_NOT_FOUND",
            f"Exchange no encontrado: exchange_id={account.exchange_id}.",
        )

    ccxt_id = ccxt_id_for(exchange_entity.name)
    if ccxt_id is None:
        raise ExchangeClientError(
            "EXCHANGE_NOT_SUPPORTED",
            f"El exchange '{exchange_entity.name}' no está soportado. "
            f"La plataforma solo opera con {PLATFORM_EXCHANGE_NAME}.",
        )
    return ccxt_id


def _new_client(ccxt_id: str, config: dict[str, Any]):
    try:
        client = getattr(ccxt, ccxt_id)({**config, "enableRateLimit": True})
        if settings.LIVE_USE_SANDBOX:
            client.set_sandbox_mode(True)
    except Exception as e:
        raise ExchangeClientError(
            "EXCHANGE_CLIENT_INIT_FAILED",
            f"No se pudo inicializar el cliente ccxt para '{ccxt_id}': {e}",
        )
    return client


def platform_credentials_configured() -> bool:
    """True si el `.env` trae las credenciales de la billetera de Binance."""
    return bool(settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET)


def build_authenticated_client(account: Account, exchange_repo: ExchangeRepository):
    """Cliente ccxt con las credenciales de la billetera de la plataforma."""
    if not platform_credentials_configured():
        raise ExchangeClientError(
            "EXCHANGE_CREDENTIALS_MISSING",
            "Faltan las credenciales de Binance en el servidor "
            "(BINANCE_API_KEY y BINANCE_API_SECRET).",
        )

    ccxt_id = resolve_ccxt_id(account, exchange_repo)
    return _new_client(
        ccxt_id,
        {"apiKey": settings.BINANCE_API_KEY, "secret": settings.BINANCE_API_SECRET},
    )


def build_public_client(account: Account, exchange_repo: ExchangeRepository):
    """Cliente ccxt sin credenciales (solo datos públicos: precios, mercados)."""
    return _new_client(resolve_ccxt_id(account, exchange_repo), {})
