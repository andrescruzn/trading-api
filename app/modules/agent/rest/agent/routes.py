# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/agent/routes.py
#
# ENDPOINT:
# - POST /agent/analyze  → Ejecuta el Prompt Maestro del agente
#
# AUTH: token requerido (cualquier usuario autenticado)
#
# RESPUESTA:
# - 200 siempre que el análisis se complete (incluso si decision=REJECTED)
# - 4xx/5xx si hay error en los datos de entrada o en la llamada al LLM
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_success_response
from app.common.security.jwt import super_admin_required, write_scope
from app.common.security.rate_limiter import agent_analysis_rate_limiter, check_user_rate_limit
from app.extensions.db import get_db
from app.modules.agent.domain.analysis_result import AnalysisResult
from app.modules.agent.providers import AgentServiceFactory

from .error_messages import AGENT_ERROR_MESSAGES
from .schemas import AnalyzeRequest

router = APIRouter(prefix="/agent", tags=["Agent"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> AgentServiceFactory:
    return AgentServiceFactory(session=db)


# ======================================================================
# Serializer
# ======================================================================

def _result_to_dict(result: AnalysisResult) -> dict[str, Any]:
    return result.to_dict()


# ======================================================================
# POST /agent/analyze
# ======================================================================

@router.post("/analyze", status_code=200)
def analyze(
    payload: AnalyzeRequest,
    identity: dict = Depends(super_admin_required),
    factory: AgentServiceFactory = Depends(get_factory),
):
    """
    Ejecuta el Prompt Maestro del agente de trading.

    Fases:
    1. Filtro de Régimen  → rechaza si el régimen no coincide
    2. Validación de Reglas → rechaza si alguna regla falla
    3. Análisis LLM → entry / SL / TP / reasoning
    4. Filtro R/R → rechaza si reward/risk < min_rr_ratio (default 2.0)

    Returns:
        200 con AnalysisResult.decision = APPROVED o REJECTED
        4xx si faltan datos (candles, features, balance)
        502 si el LLM falla
    """
    # Cada análisis es una llamada de pago al LLM: límite por usuario
    check_user_rate_limit(agent_analysis_rate_limiter, identity["user_id"])

    result = factory.analyze().analyze(
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        strategy_id=payload.strategy_id,
        account_id=payload.account_id,
        feature_set_id=payload.feature_set_id,
        owner_id=write_scope(identity),
    )

    if not result.success:
        return build_error_response(result, AGENT_ERROR_MESSAGES)

    decision = result.data.decision
    msg = "Análisis completado: operación APROBADA." if decision == "APPROVED" \
        else "Análisis completado: operación RECHAZADA."

    return build_success_response(
        data=_result_to_dict(result.data),
        msg=msg,
    )
