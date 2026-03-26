# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/investor_repository.py
#
# Contrato (Protocol) para el repositorio de Investor.
# La infraestructura implementa este protocolo sin heredar de él.
# ======================================================================

from __future__ import annotations

from typing import Protocol

from app.modules.billing.domain.investor_entity import Investor


class InvestorRepository(Protocol):
    """Contrato para el repositorio de inversores."""

    def find_by_id(self, investor_id: int) -> Investor | None: ...

    def find_by_user_id(self, user_id: int) -> Investor | None: ...

    def list_all(self, only_active: bool = False) -> list[Investor]: ...

    def save(self, investor: Investor) -> Investor: ...
