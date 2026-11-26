# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/rest/backtests/schemas.py
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class RunBacktestRequest(BaseModel):
    strategy_id: int = Field(..., gt=0)
    symbol_id: int = Field(..., gt=0)
    timeframe_id: int = Field(..., gt=0)
    bars: int = Field(default=1500, ge=300, le=3000, description="Velas a simular")
    initial_capital: Decimal = Field(
        default=Decimal("10000"), gt=0, le=Decimal("100000000"), max_digits=30, decimal_places=12
    )
    fee_pct: Decimal = Field(
        default=Decimal("0.001"), ge=0, le=Decimal("0.01"), description="Comisión por lado (0.001 = 0,1 %)"
    )
