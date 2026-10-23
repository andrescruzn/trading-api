# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/fees/fee_schedule_service.py
#
# CASOS DE USO:
# - current()  → tabla de tramos vigente (cualquier participante: la
#                comisión es transparente para todos).
# - history()  → versiones anteriores (staff).
# - create(..) → un super admin publica una tabla nueva (versión nueva; las
#                salidas ya liquidadas guardan la versión que usaron).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.fund.domain.commission import FeeSchedule, FeeTier, valid_tiers
from app.modules.fund.domain.payout_repositories import FeeScheduleRepository


class FeeScheduleService:

    def __init__(self, *, repo: FeeScheduleRepository):
        self._repo = repo

    def current(self) -> ServiceResult[FeeSchedule | None]:
        return ServiceResult.ok(self._repo.current())

    def history(self) -> ServiceResult[list[FeeSchedule]]:
        return ServiceResult.ok(self._repo.list_all())

    def create(
        self, *, tiers: list[FeeTier], note: str | None, requester_user_id: int
    ) -> ServiceResult[FeeSchedule]:
        ordered = sorted(tiers, key=lambda t: t.from_return)
        if not valid_tiers(ordered):
            return ServiceResult.fail(code="FUND_FEE_INVALID_TIERS", http_status=422)
        try:
            saved = self._repo.create(
                FeeSchedule(
                    id=0,
                    tiers=ordered,
                    note=(note or "").strip()[:500] or None,
                    created_by_user_id=int(requester_user_id),
                )
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(saved)
