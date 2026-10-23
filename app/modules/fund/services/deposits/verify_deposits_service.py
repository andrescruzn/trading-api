# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/deposits/verify_deposits_service.py
#
# CASO DE USO:
# - Revisar las solicitudes `pending` contra los depósitos del exchange.
#   Lo llama el scheduler (cada WALLET_SYNC_INTERVAL_SECONDS) y "Verificar
#   ahora" de un super admin.
#
# REGLAS (por solicitud, emparejando por txid):
# - No aparece → sigue pendiente; vencida (`expires_at`) → `expired`.
# - Aparece `pending` en el exchange → espera a la siguiente vuelta.
# - `failed` / `canceled` en el exchange, o de otra moneda → `review`.
# - Monto acreditado fuera de la tolerancia de lo declarado → `review`.
# - Monto > `deposit_auto_confirm_max` → `review` (lo decide un super admin).
# - Si no → `confirmed` automático: se acredita lo que reporta el exchange al
#   saldo pendiente de asignar.
# - Billetera paper: no hay exchange; solo vencen (se confirman a mano).
# ======================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.accounts.domain.wallet_gateway import (
    ExchangeDeposit,
    WalletGateway,
    WalletGatewayError,
)
from app.modules.fund.domain.deposit_request_entity import (
    DepositRequest,
    amounts_match,
    normalize_txid,
)
from app.modules.fund.domain.fund_repositories import (
    DepositRequestRepository,
    FundSettingsRepository,
    LedgerRepository,
)
from app.modules.fund.services.deposits.deposit_crediting import DepositCreditor
from app.modules.fund.services.wallet_context import WalletContextResolver

logger = logging.getLogger(__name__)

# Margen hacia atrás al pedir depósitos al exchange (la persona puede
# registrar el txid un tiempo después de enviarlo)
_LOOKBACK = timedelta(days=2)


@dataclass
class VerifySummary:
    checked: int = 0
    confirmed: int = 0
    review: int = 0
    expired: int = 0
    waiting: int = 0


class VerifyDepositsService:

    def __init__(
        self,
        *,
        deposit_repo: DepositRequestRepository,
        ledger_repo: LedgerRepository,
        settings_repo: FundSettingsRepository,
        wallet_resolver: WalletContextResolver,
        gateway: WalletGateway,
    ):
        self._deposit_repo = deposit_repo
        self._settings_repo = settings_repo
        self._wallet_resolver = wallet_resolver
        self._gateway = gateway
        self._creditor = DepositCreditor(deposit_repo, ledger_repo)

    def verify(self) -> ServiceResult[VerifySummary]:
        pending = self._deposit_repo.list_by_statuses(["pending"])
        summary = VerifySummary(checked=len(pending))
        if not pending:
            return ServiceResult.ok(summary)

        context, error = self._wallet_resolver.resolve()
        if context is None:
            return ServiceResult.fail(code=error, http_status=409)

        now = utc_now()
        found: dict[str, ExchangeDeposit] = {}
        if context.is_live:
            since = min(r.created_at or now for r in pending) - _LOOKBACK
            try:
                deposits = self._gateway.fetch_deposits(context.account, context.asset, since)
            except WalletGatewayError as exc:
                logger.warning("[Fund] No se pudieron leer los depósitos (%s): %s", exc.code, exc)
                return ServiceResult.fail(code=exc.code, http_status=502)
            found = {normalize_txid(d.txid): d for d in deposits}

        settings = self._settings_repo.get()
        try:
            for request in pending:
                deposit = found.get(request.txid)
                if deposit is None:
                    if request.is_expired(now):
                        request.status = "expired"
                        request.resolved_at = now
                        if self._deposit_repo.update_if_status(request, ["pending"]):
                            summary.expired += 1
                    else:
                        summary.waiting += 1
                    continue
                self._apply(
                    request, deposit, context.asset, settings.deposit_auto_confirm_max, now, summary
                )
            self._deposit_repo.commit()
        except Exception:
            self._deposit_repo.rollback()
            raise
        return ServiceResult.ok(summary)

    def _apply(
        self,
        request: DepositRequest,
        deposit: ExchangeDeposit,
        asset: str,
        auto_max: Decimal,
        now: datetime,
        summary: VerifySummary,
    ) -> None:
        request.exchange_status = deposit.status
        request.exchange_deposit_id = deposit.exchange_id
        request.address_from = deposit.address_from

        if deposit.status == "pending":
            # Aún sin confirmaciones en la red: solo se guarda lo visto
            self._deposit_repo.update_if_status(request, ["pending"])
            summary.waiting += 1
            return

        request.credited_amount = deposit.amount
        reason = None
        if deposit.status != "ok":
            reason = "exchange_failed"
        elif deposit.asset.upper() != asset:
            reason = "wrong_asset"
        elif not amounts_match(request.declared_amount, deposit.amount):
            reason = "amount_mismatch"
        elif deposit.amount > auto_max:
            reason = "over_threshold"

        if reason is not None:
            request.status = "review"
            request.review_reason = reason
            if self._deposit_repo.update_if_status(request, ["pending"]):
                summary.review += 1
            return

        if self._creditor.confirm(
            request,
            amount=deposit.amount,
            now=now,
            expected=["pending"],
            resolved_by_user_id=None,
            note=None,
        ):
            summary.confirmed += 1
