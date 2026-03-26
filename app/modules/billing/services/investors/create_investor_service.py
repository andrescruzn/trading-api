# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/services/investors/create_investor_service.py
#
# Crea un nuevo inversor asociado a un user_id existente (role=investor).
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.contracts.service_result import ServiceResult
from app.modules.billing.domain.investor_entity import Investor
from app.modules.billing.domain.investor_repository import InvestorRepository


class CreateInvestorService:
    """
    Crea el perfil de inversor para un usuario con role_id=investor.

    Reglas de negocio:
    - user_id debe ser único: un usuario no puede tener dos perfiles de inversor.
    - fee_pct debe estar entre 0 y 1 (0% a 100%).
    """

    def __init__(self, repo: InvestorRepository, session: Session):
        self._repo = repo
        self._session = session

    def execute(
        self,
        user_id: int,
        fee_pct: Decimal,
    ) -> ServiceResult[Investor]:
        # Validar fee_pct
        if not (Decimal("0") <= fee_pct <= Decimal("1")):
            return ServiceResult.fail(
                code="BILLING_INVALID_FEE_PCT",
                http_status=422,
            )

        # Verificar que no exista ya un perfil para este user_id
        existing = self._repo.find_by_user_id(user_id)
        if existing:
            return ServiceResult.fail(
                code="BILLING_INVESTOR_ALREADY_EXISTS",
                http_status=409,
            )

        investor = Investor(id=0, user_id=user_id, fee_pct=fee_pct)
        saved = self._repo.save(investor)
        self._session.commit()
        return ServiceResult.ok(data=saved)
