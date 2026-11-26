# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/settings/deposit_networks_service.py
#
# CASOS DE USO (super admin):
# - list_available() → redes por las que el exchange acepta la moneda del
#                      fondo (para elegir cuáles se ofrecen).
# - set(networks)    → guarda las redes aceptadas con su dirección.
#
# REGLAS:
# - Billetera live: la dirección SIEMPRE se lee del exchange. Escribirla a
#   mano es la forma más fácil de que un error de tipeo mande dinero a una
#   dirección ajena, así que se ignora cualquier dirección enviada.
# - Billetera paper (desarrollo): no hay exchange; la dirección se escribe
#   a mano y solo sirve para probar el flujo.
# - Sin redes = no se puede depositar (la página lo explica).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.wallet_gateway import (
    DepositNetwork,
    WalletGateway,
    WalletGatewayError,
)
from app.modules.fund.domain.fund_repositories import FundSettingsRepository
from app.modules.fund.domain.fund_settings_entity import DepositNetworkConfig, FundSettings
from app.modules.fund.services.wallet_context import WalletContext, WalletContextResolver

MAX_NETWORKS = 10


@dataclass(frozen=True)
class NetworkChoice:
    """Red elegida; `address`/`tag` solo se usan con billetera paper."""

    network: str
    name: str | None = None
    address: str | None = None
    tag: str | None = None


@dataclass(frozen=True)
class AvailableNetworks:
    asset: str
    is_live: bool
    networks: list[DepositNetwork]


class DepositNetworksService:

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

    def list_available(self) -> ServiceResult[AvailableNetworks]:
        context, error = self._wallet_resolver.resolve()
        if context is None:
            return ServiceResult.fail(code=error, http_status=409)
        if not context.is_live:
            return ServiceResult.ok(AvailableNetworks(context.asset, False, []))
        try:
            networks = self._gateway.fetch_deposit_networks(context.account, context.asset)
        except WalletGatewayError as exc:
            return ServiceResult.fail(code=exc.code, http_status=502)
        return ServiceResult.ok(AvailableNetworks(context.asset, True, networks))

    def set(
        self, networks: list[NetworkChoice], requester_user_id: int
    ) -> ServiceResult[FundSettings]:
        context, error = self._wallet_resolver.resolve()
        if context is None:
            return ServiceResult.fail(code=error, http_status=409)

        codes = [n.network.strip() for n in networks]
        if len(codes) > MAX_NETWORKS or len(set(codes)) != len(codes) or any(not c for c in codes):
            return ServiceResult.fail(code="FUND_INVALID_NETWORKS", http_status=422)

        try:
            configs = (
                self._from_exchange(context, codes)
                if context.is_live
                else self._from_input(networks)
            )
        except WalletGatewayError as exc:
            return ServiceResult.fail(code=exc.code, http_status=502)
        if configs is None:
            return ServiceResult.fail(code="FUND_INVALID_NETWORKS", http_status=422)

        settings = self._settings_repo.get()
        settings.deposit_networks = configs
        settings.updated_by_user_id = int(requester_user_id)
        try:
            saved = self._settings_repo.save(settings)
            self._settings_repo.commit()
        except Exception:
            self._settings_repo.rollback()
            raise
        return ServiceResult.ok(saved)

    def _from_exchange(
        self, context: WalletContext, codes: list[str]
    ) -> list[DepositNetworkConfig] | None:
        available = {
            n.code: n
            for n in self._gateway.fetch_deposit_networks(context.account, context.asset)
        }
        configs: list[DepositNetworkConfig] = []
        for code in codes:
            network = available.get(code)
            if network is None or not network.deposit_enabled:
                return None
            address = self._gateway.fetch_deposit_address(context.account, context.asset, code)
            configs.append(
                DepositNetworkConfig(code, network.name, address.address, address.tag)
            )
        return configs

    @staticmethod
    def _from_input(networks: list[NetworkChoice]) -> list[DepositNetworkConfig] | None:
        configs: list[DepositNetworkConfig] = []
        for n in networks:
            address = (n.address or "").strip()
            if not address:
                return None
            configs.append(
                DepositNetworkConfig(
                    n.network.strip(),
                    (n.name or n.network).strip(),
                    address,
                    (n.tag or "").strip() or None,
                )
            )
        return configs
