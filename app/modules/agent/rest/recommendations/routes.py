# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/recommendations/routes.py
#
# ENDPOINTS:
# - GET  /recommendations/markets/latest → última recomendación de la IA
#                                          (autenticado). Responde
#                                          {recommendation: {...} | null}:
#                                          `send` convierte un data None en [].
# - POST /recommendations/markets        → pide recomendaciones nuevas a
#                                          la IA (solo super admin, con
#                                          límite por minuto)
#
# NOTAS:
# - El POST llama al LLM (puede tardar decenas de segundos y tiene coste):
#   ruta síncrona para que corra en el threadpool.
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_created_response, build_error_response, build_success_response
from app.common.security.jwt import token_required_actual
from app.common.security.jwt.role_guard import super_admin_required
from app.common.security.rate_limiter import check_user_rate_limit, recommendation_rate_limiter
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.agent.domain.market_recommendation_entity import MarketRecommendation
from app.modules.agent.providers import AgentServiceFactory

from .error_messages import RECOMMENDATION_ERROR_MESSAGES
from .schemas import GenerateMarketRecommendationsRequest

router = APIRouter(prefix="/recommendations", tags=["Agent — Recommendations"])


def get_factory(db: Session = Depends(get_db)) -> AgentServiceFactory:
    return AgentServiceFactory(session=db)


def _recommendation_to_dict(rec: MarketRecommendation) -> dict[str, Any]:
    return {
        "id": rec.id,
        "created_at": to_iso_utc(rec.created_at) if rec.created_at else None,
        "asset_class": rec.asset_class,
        "summary": rec.summary,
        "items": [item.to_dict() for item in rec.items],
        "llm_provider": rec.llm_provider,
        "llm_model": rec.llm_model,
        "llm_latency_ms": rec.llm_latency_ms,
    }


# ======================================================================
# GET /recommendations/markets/latest
# ======================================================================

@router.get("/markets/latest", status_code=200)
def get_latest_market_recommendation(
    _identity: dict = Depends(token_required_actual),
    factory: AgentServiceFactory = Depends(get_factory),
):
    """Última recomendación de mercados de la IA; `recommendation` es null si aún no hay."""
    result = factory.get_latest_market_recommendation().get()
    if not result.success:
        return build_error_response(result, RECOMMENDATION_ERROR_MESSAGES)
    rec = _recommendation_to_dict(result.data) if result.data else None
    return build_success_response(data={"recommendation": rec})


# ======================================================================
# POST /recommendations/markets
# ======================================================================

@router.post("/markets", status_code=201)
def generate_market_recommendations(
    payload: GenerateMarketRecommendationsRequest,
    identity: dict = Depends(super_admin_required),
    factory: AgentServiceFactory = Depends(get_factory),
):
    """Pide a la IA en qué mercados crear agentes y guarda la respuesta. Solo super admin."""
    check_user_rate_limit(recommendation_rate_limiter, identity["user_id"])

    result = factory.generate_market_recommendations().generate(
        user_id=identity["user_id"],
        asset_class=payload.asset_class,
    )
    if not result.success:
        return build_error_response(result, RECOMMENDATION_ERROR_MESSAGES)
    return build_created_response(
        data=_recommendation_to_dict(result.data),
        msg="Recomendaciones listas.",
    )
