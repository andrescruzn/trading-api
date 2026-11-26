# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/deposits/create_deposit_request_service.py
#
# CASO DE USO:
# - Un participante (super admin, socio o inversor) registra que envió
#   dinero a la billetera: red, txid y monto. La verificación contra el
#   exchange la hace después VerifyDepositsService.
#
# REGLAS:
# - Solo redes aceptadas en los ajustes del fondo.
# - txid válido y único en todo el fondo (nadie reclama dos veces el mismo
#   depósito ni el de otra persona).
# - Máximo MAX_OPEN_REQUESTS solicitudes abiertas por persona.
# - Vence a las `deposit_request_ttl_hours` si nunca aparece en el exchange.
# ======================================================================

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.fund.domain.deposit_request_entity import (
    DepositRequest,
    is_valid_txid,
    normalize_txid,
)
from app.modules.fund.domain.fund_repositories import (
    DepositRequestRepository,
    FundSettingsRepository,
)
from app.modules.fund.services.wallet_context import WalletContextResolver

MAX_OPEN_REQUESTS = 10
MAX_DEPOSIT_AMOUNT = Decimal("1000000000")


class CreateDepositRequestService:

    def __init__(
        self,
        *,
        deposit_repo: DepositRequestRepository,
        settings_repo: FundSettingsRepository,
        wallet_resolver: WalletContextResolver,
    ):
        self._deposit_repo = deposit_repo
        self._settings_repo = settings_repo
        self._wallet_resolver = wallet_resolver

    def create(
        self,
        *,
        user_id: int,
        network: str,
        txid: str,
        amount: Decimal,
    ) -> ServiceResult[DepositRequest]:
        context, error = self._wallet_resolver.resolve()
        if context is None:
            return ServiceResult.fail(code=error, http_status=409)

        settings = self._settings_repo.get()
        if settings.network((network or "").strip()) is None:
            return ServiceResult.fail(code="FUND_DEPOSIT_INVALID_NETWORK", http_status=422)

        clean_txid = normalize_txid(txid)
        if not is_valid_txid(clean_txid):
            return ServiceResult.fail(code="FUND_DEPOSIT_INVALID_TXID", http_status=422)

        if amount <= 0 or amount > MAX_DEPOSIT_AMOUNT:
            return ServiceResult.fail(code="FUND_DEPOSIT_INVALID_AMOUNT", http_status=422)

        if self._deposit_repo.get_by_txid(clean_txid) is not None:
            return ServiceResult.fail(code="FUND_DEPOSIT_TXID_TAKEN", http_status=409)

        if self._deposit_repo.count_open_by_user(user_id) >= MAX_OPEN_REQUESTS:
            return ServiceResult.fail(code="FUND_DEPOSIT_TOO_MANY_OPEN", http_status=409)

        now = utc_now()
        request = DepositRequest(
            id=0,
            user_id=int(user_id),
            asset=context.asset,
            network=network.strip(),
            txid=clean_txid,
            declared_amount=amount,
            expires_at=now + timedelta(hours=settings.deposit_request_ttl_hours),
        )
        try:
            created = self._deposit_repo.create(request)
            self._deposit_repo.commit()
        except Exception:
            self._deposit_repo.rollback()
            raise
        return ServiceResult.ok(created)
