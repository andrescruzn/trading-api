# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/wallet_gateway.py
#
# Contrato con el exchange de la billetera de la plataforma.
# Implementado en infrastructure/ccxt_wallet_gateway.py (ccxt).
#
# DECISIÓN:
# - Es una Strategy por exchange: la billetera puede ser Binance, Bybit u
#   otro exchange de ccxt; uno sin ccxt (p. ej. eToro) necesita su propia
#   implementación de este contrato.
# - Los errores salen como `WalletGatewayError(code)`: el servicio los
#   traduce a ServiceResult y la ruta a texto de UI.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.wallet_snapshot_entity import AssetBalance


class WalletGatewayError(Exception):
    """Fallo al hablar con el exchange; `code` es un código estable de error."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code


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
