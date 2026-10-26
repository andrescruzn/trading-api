# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/payouts/withdraw_networks.py
#
# PROPÓSITO:
# - Redes por las que el fondo envía los retiros: las mismas que el super
#   admin aceptó para depositar (`fund_settings.deposit_networks`). Con la
#   billetera live se completan con la comisión y el mínimo de retiro que
#   cobra Binance en cada red.
#
# NOTAS:
# - Leer las comisiones es "mejor esfuerzo": si Binance no responde, las
#   redes salen sin comisión y sin mínimo (se registra en el log), para no
#   frenar a nadie por un fallo pasajero del exchange.
# ======================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from app.modules.accounts.domain.wallet_gateway import WalletGateway, WalletGatewayError
from app.modules.fund.domain.fund_repositories import FundSettingsRepository
from app.modules.fund.domain.withdrawal_entity import normalize_network
from app.modules.fund.services.wallet_context import WalletContextResolver

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WithdrawNetworkInfo:
    network: str
    name: str
    fee: Decimal | None = None
    min_amount: Decimal | None = None
    # False si Binance tiene la red suspendida para retiros hoy
    enabled: bool = True


@dataclass(frozen=True)
class WithdrawNetworks:
    asset: str
    is_live: bool
    networks: list[WithdrawNetworkInfo]

    def find(self, network: str | None) -> WithdrawNetworkInfo | None:
        code = normalize_network(network)
        return next((item for item in self.networks if item.network == code), None)


class WithdrawNetworksReader:

    def __init__(
        self,
        *,
        settings_repo: FundSettingsRepository,
        wallet_resolver: WalletContextResolver,
        gateway: WalletGateway,
    ):
        self._settings_repo = settings_repo
        self._wallet_resolver = wallet_resolver
        self._gateway = gateway

    def read(self) -> tuple[WithdrawNetworks | None, str | None]:
        """Las redes de retiro, o el código de error de la billetera."""
        context, error = self._wallet_resolver.resolve()
        if context is None:
            return None, error
        configured = self._settings_repo.get().deposit_networks
        exchange = {}
        if context.is_live and configured:
            try:
                exchange = {
                    normalize_network(item.code): item
                    for item in self._gateway.fetch_withdraw_networks(context.account, context.asset)
                }
            except WalletGatewayError as exc:
                logger.warning("[Fund] No se pudieron leer las redes de retiro (%s): %s", exc.code, exc)

        networks: list[WithdrawNetworkInfo] = []
        for item in configured:
            code = normalize_network(item.network)
            live = exchange.get(code)
            networks.append(
                WithdrawNetworkInfo(
                    network=code,
                    name=item.name or code,
                    fee=live.fee if live else None,
                    min_amount=live.min_amount if live else None,
                    enabled=live.withdraw_enabled if live else True,
                )
            )
        return WithdrawNetworks(asset=context.asset, is_live=context.is_live, networks=networks), None
