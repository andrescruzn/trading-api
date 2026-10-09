# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/rest/bots/schemas.py
# ======================================================================

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateBotRequest(BaseModel):
    name:           str            = Field(..., min_length=1, max_length=80)
    strategy_id:    int            = Field(..., gt=0)
    symbol_id:      int            = Field(..., gt=0)
    timeframe_id:   int            = Field(..., gt=0)
    account_id:     int            = Field(..., gt=0)
    feature_set_id: int            = Field(..., gt=0)
    mode:           str            = Field(..., pattern="^(paper|live)$")
    risk_params:    dict[str, Any] = Field(
        ...,
        description=(
            "Parámetros de riesgo del bot. "
            "Campo obligatorio: risk_pct (fracción > 0 y <= 0.01, regla del 1 %). "
            "Campo opcional: max_drawdown_pct (float entre 0 y 1)."
        ),
    )


class UpdateBotRequest(BaseModel):
    name:        str | None            = Field(default=None, min_length=1, max_length=80)
    mode:        str | None            = Field(default=None, pattern="^(paper|live)$")
    risk_params: dict[str, Any] | None = Field(default=None)
