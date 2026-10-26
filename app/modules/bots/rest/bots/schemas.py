# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/rest/bots/schemas.py
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class CreateBotRequest(BaseModel):
    name:           str            = Field(..., min_length=1, max_length=80)
    strategy_id:    int            = Field(..., gt=0)
    symbol_id:      int            = Field(..., gt=0)
    timeframe_id:   int            = Field(..., gt=0)
    feature_set_id: int            = Field(..., gt=0)
    mode:           str            = Field(
        ...,
        pattern="^(paper|live)$",
        description="live = agente real (billetera de Binance) · paper = agente demo.",
    )
    demo_capital:   Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=22,
        decimal_places=8,
        description="Solo agentes demo: monto simulado a invertir (moneda de cotización).",
    )
    risk_params:    dict[str, Any] = Field(
        ...,
        max_length=20,
        description=(
            "Parámetros de riesgo del bot. "
            "Campo obligatorio: risk_pct (fracción > 0 y <= 0.01, regla del 1 %). "
            "Campo opcional: max_drawdown_pct (float entre 0 y 1)."
        ),
    )
    execution_mode: str = Field(default="manual", pattern="^(manual|approval|auto)$")
    approval_ttl_minutes: int | None = Field(default=None, ge=1, le=1440)


class UpdateBotRequest(BaseModel):
    name:        str | None            = Field(default=None, min_length=1, max_length=80)
    risk_params: dict[str, Any] | None = Field(default=None, max_length=20)
    execution_mode: str | None = Field(default=None, pattern="^(manual|approval|auto)$")
    approval_ttl_minutes: int | None = Field(default=None, ge=1, le=1440)
    share_signals: bool | None = Field(
        default=None,
        description="Otros usuarios pueden suscribirse a sus señales aprobadas (Telegram).",
    )
