# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/rest/investors/schemas.py
# ======================================================================

from decimal import Decimal

from pydantic import BaseModel, Field


class CreateInvestorRequest(BaseModel):
    user_id: int = Field(description="ID del usuario con role=investor")
    fee_pct: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Performance fee entre 0 y 1 (ej: 0.20 = 20%)",
    )


class UpdateInvestorRequest(BaseModel):
    fee_pct: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Nuevo porcentaje de fee",
    )
    is_active: bool | None = Field(default=None, description="Activar/desactivar inversor")
