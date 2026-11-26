# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/settings/fund_settings_service.py
#
# CASOS DE USO:
# - get()          → ajustes completos (staff).
# - deposit_info() → lo que necesita un participante para depositar: moneda,
#                    redes con la dirección de la billetera y permanencia
#                    mínima (cualquier persona con sesión).
# - update(...)    → un super admin cambia permanencia, tope de confirmación
#                    automática y vencimiento de solicitudes.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.fund.domain.fund_repositories import FundSettingsRepository
from app.modules.fund.domain.fund_settings_entity import (
    MAX_DEPOSIT_REQUEST_TTL_HOURS,
    MAX_MIN_HOLD_DAYS,
    DepositNetworkConfig,
    FundSettings,
)
from app.modules.fund.services.wallet_context import WalletContextResolver


@dataclass(frozen=True)
class DepositInfo:
    """Instrucciones para depositar. `enabled` False = aún no se puede depositar."""

    enabled: bool
    asset: str | None
    networks: list[DepositNetworkConfig]
    min_hold_days: int
    request_ttl_hours: int


class FundSettingsService:

    def __init__(
        self,
        *,
        settings_repo: FundSettingsRepository,
        wallet_resolver: WalletContextResolver,
    ):
        self._settings_repo = settings_repo
        self._wallet_resolver = wallet_resolver

    def get(self) -> ServiceResult[FundSettings]:
        return ServiceResult.ok(self._settings_repo.get())

    def deposit_info(self) -> ServiceResult[DepositInfo]:
        settings = self._settings_repo.get()
        context, _ = self._wallet_resolver.resolve()
        return ServiceResult.ok(
            DepositInfo(
                enabled=context is not None and bool(settings.deposit_networks),
                asset=context.asset if context else None,
                networks=settings.deposit_networks if context else [],
                min_hold_days=settings.min_hold_days,
                request_ttl_hours=settings.deposit_request_ttl_hours,
            )
        )

    def update(
        self,
        *,
        min_hold_days: int,
        deposit_auto_confirm_max: Decimal,
        deposit_request_ttl_hours: int,
        requester_user_id: int,
    ) -> ServiceResult[FundSettings]:
        if not 0 <= int(min_hold_days) <= MAX_MIN_HOLD_DAYS:
            return ServiceResult.fail(code="FUND_INVALID_MIN_HOLD_DAYS", http_status=422)
        if deposit_auto_confirm_max < 0:
            return ServiceResult.fail(code="FUND_INVALID_AUTO_CONFIRM_MAX", http_status=422)
        if not 1 <= int(deposit_request_ttl_hours) <= MAX_DEPOSIT_REQUEST_TTL_HOURS:
            return ServiceResult.fail(code="FUND_INVALID_REQUEST_TTL", http_status=422)

        settings = self._settings_repo.get()
        settings.min_hold_days = int(min_hold_days)
        settings.deposit_auto_confirm_max = deposit_auto_confirm_max
        settings.deposit_request_ttl_hours = int(deposit_request_ttl_hours)
        settings.updated_by_user_id = int(requester_user_id)
        try:
            saved = self._settings_repo.save(settings)
            self._settings_repo.commit()
        except Exception:
            self._settings_repo.rollback()
            raise
        return ServiceResult.ok(saved)
