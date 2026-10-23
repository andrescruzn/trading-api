# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/exchange_client.py
#
# PROPÓSITO:
# - Armar el cliente ccxt de una cuenta: con sus credenciales descifradas
#   (órdenes live de M8, saldo de la billetera) o sin ellas (precios
#   públicos). Un solo sitio para descifrar credenciales y respetar
#   LIVE_USE_SANDBOX.
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
from app.common.security.credentials_cipher import CredentialsCipher
from app.modules.accounts.domain.account_entity import Account
from app.modules.market.domain.ccxt_exchanges import CCXT_EXCHANGE_MAP, ccxt_id_for
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
            "La cuenta no tiene un exchange asociado. "
            "Configura el exchange desde la página de cuentas.",
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
            f"El exchange '{exchange_entity.name}' no está soportado para live trading. "
            f"Exchanges disponibles: {', '.join(CCXT_EXCHANGE_MAP.keys())}.",
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


def build_authenticated_client(
    account: Account,
    exchange_repo: ExchangeRepository,
    cipher: CredentialsCipher,
):
    """Cliente ccxt con las credenciales (descifradas) de la cuenta."""
    enc_creds = account.meta.get("enc_creds")
    if not enc_creds:
        raise ExchangeClientError(
            "ACCOUNT_NO_CREDENTIALS",
            "La cuenta no tiene credenciales API configuradas. "
            "Agrega api_key y api_secret desde la página de cuentas.",
        )

    try:
        creds = cipher.decrypt(enc_creds)
    except Exception:
        raise ExchangeClientError(
            "ACCOUNT_CREDENTIALS_UNREADABLE",
            "No se pudieron descifrar las credenciales API. "
            "Reconfigura las credenciales de la cuenta.",
        )

    api_key: str = creds.get("api_key", "")
    api_secret: str = creds.get("api_secret", "")
    if not api_key or not api_secret:
        raise ExchangeClientError(
            "ACCOUNT_CREDENTIALS_INCOMPLETE",
            "Las credenciales API están incompletas (api_key o api_secret vacíos).",
        )

    ccxt_id = resolve_ccxt_id(account, exchange_repo)
    return _new_client(ccxt_id, {"apiKey": api_key, "secret": api_secret})


def build_public_client(account: Account, exchange_repo: ExchangeRepository):
    """Cliente ccxt sin credenciales (solo datos públicos: precios, mercados)."""
    return _new_client(resolve_ccxt_id(account, exchange_repo), {})
