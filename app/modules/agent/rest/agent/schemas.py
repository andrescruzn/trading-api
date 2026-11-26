# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/agent/schemas.py
#
# Schemas Pydantic para el endpoint de análisis del agente.
# ======================================================================

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Payload para POST /agent/analyze."""

    symbol_id: int = Field(..., ge=1, description="ID del símbolo a analizar")
    timeframe_id: int = Field(..., ge=1, description="ID del timeframe")
    strategy_id: int = Field(..., ge=1, description="ID de la estrategia a aplicar")
    account_id: int = Field(..., ge=1, description="ID de la cuenta (capital y risk_pct)")
    feature_set_id: int = Field(
        ..., ge=1, description="ID del feature set con los indicadores calculados"
    )
