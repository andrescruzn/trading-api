# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/rest/strategies/schemas.py
#
# Schemas Pydantic para los endpoints de estrategias.
# ======================================================================

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateStrategyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    version: str = Field(default="1.0.0", max_length=32)
    description: str | None = Field(default=None)
    parameters: dict[str, Any] = Field(
        ...,
        description=(
            "Configuración JSON de la estrategia. Campos mínimos: "
            "strategy_type (trend_following|mean_reversion), "
            "regime_required (trend_up|trend_down|sideways|null), "
            "timeframe_code (ej: '1h'), rules (lista de reglas)."
        ),
    )


class UpdateStrategyRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    version: str | None = Field(default=None, max_length=32)
    description: str | None = Field(default=None)
    parameters: dict[str, Any] | None = Field(default=None)
