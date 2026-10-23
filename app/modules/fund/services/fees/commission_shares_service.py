# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/fees/commission_shares_service.py
#
# CASOS DE USO:
# - current() / history() → reparto vigente y anteriores (staff).
# - set(...)              → un super admin publica un reparto nuevo.
# - earnings()            → comisión acumulada de cada propietario (staff).
# - mine(user_id)         → las comisiones que recibió una persona.
#
# REGLAS:
# - Solo propietarios reciben comisión: super admin y socios (decisión del
#   usuario: el socio recibe un % configurable).
# - Los % suman exactamente 100 %. Cambiar el reparto no reescribe las
#   comisiones ya acreditadas (cada salida guarda su versión).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.fund.domain.agent_pool_entity import CommissionCredit
from app.modules.fund.domain.commission import (
    CommissionShare,
    CommissionShareVersion,
    valid_shares,
)
from app.modules.fund.domain.payout_repositories import (
    CommissionCreditRepository,
    CommissionShareRepository,
)
from app.modules.users.domain import UserRepository


@dataclass(frozen=True)
class OwnerEarning:
    user_id: int
    commissions: Decimal


class CommissionSharesService:

    def __init__(
        self,
        *,
        repo: CommissionShareRepository,
        credit_repo: CommissionCreditRepository,
        user_repo: UserRepository,
        owner_role_ids: frozenset[int],
    ):
        self._repo = repo
        self._credit_repo = credit_repo
        self._user_repo = user_repo
        self._owner_role_ids = owner_role_ids

    def current(self) -> ServiceResult[CommissionShareVersion | None]:
        return ServiceResult.ok(self._repo.current())

    def history(self) -> ServiceResult[list[CommissionShareVersion]]:
        return ServiceResult.ok(self._repo.list_all())

    def set(
        self, *, shares: list[CommissionShare], note: str | None, requester_user_id: int
    ) -> ServiceResult[CommissionShareVersion]:
        if not valid_shares(shares):
            return ServiceResult.fail(code="FUND_SHARES_INVALID", http_status=422)
        for share in shares:
            user = self._user_repo.get_by_id(share.user_id)
            if user is None or int(user.role_id) not in self._owner_role_ids:
                return ServiceResult.fail(
                    code="FUND_SHARES_NOT_OWNER",
                    http_status=422,
                    meta={"user_id": share.user_id},
                )
        try:
            saved = self._repo.create(
                CommissionShareVersion(
                    id=0,
                    shares=sorted(shares, key=lambda s: s.user_id),
                    note=(note or "").strip()[:500] or None,
                    created_by_user_id=int(requester_user_id),
                )
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(saved)

    def earnings(self) -> ServiceResult[list[OwnerEarning]]:
        totals = self._credit_repo.totals_by_user()
        return ServiceResult.ok(
            sorted(
                (OwnerEarning(user_id, amount) for user_id, amount in totals.items()),
                key=lambda e: e.commissions,
                reverse=True,
            )
        )

    def mine(self, user_id: int) -> ServiceResult[list[CommissionCredit]]:
        return ServiceResult.ok(self._credit_repo.list_by_user(int(user_id)))
