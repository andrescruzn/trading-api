# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/investor_entity.py
#
# Entidad de dominio: Investor.
# Extiende a un User (role_id=3) con datos de negocio del inversor:
# la tasa de performance fee y si está activo.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal


class Investor:
    """
    Entidad de dominio: Investor.

    Un inversor ES un usuario con role_id=3.
    Esta entidad contiene los datos de negocio adicionales:
    - fee_pct: porcentaje de performance fee (ej: Decimal('0.2000') = 20%)
    - is_active: si el inversor está operativo
    """

    def __init__(
        self,
        id: int,
        user_id: int,
        fee_pct: Decimal,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.fee_pct = fee_pct
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    def is_valid_fee_pct(self) -> bool:
        """El fee debe estar entre 0% y 100%."""
        return Decimal("0") <= self.fee_pct <= Decimal("1")

    def fee_as_percentage(self) -> str:
        """Representación legible: 0.2000 → '20.00%'."""
        return f"{self.fee_pct * 100:.2f}%"
