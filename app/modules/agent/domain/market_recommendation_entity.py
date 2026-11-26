# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/domain/market_recommendation_entity.py
#
# Entidad de dominio: MarketRecommendation.
# Una consulta a la IA sobre en qué mercados conviene crear un agente,
# a partir del ranking del explorador (M2) y de las estrategias (M5).
#
# NOTAS:
# - `items` solo guarda recomendaciones que pasaron el filtro
#   determinista del servicio (símbolo candidato, estrategia existente y
#   coherente con la tendencia). Lo que la IA inventó no llega aquí.
# - `market_snapshot` guarda los datos que se le enviaron a la IA, para
#   poder auditar por qué recomendó lo que recomendó.
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RecommendationItem:
    """Un mercado recomendado, con la estrategia sugerida."""

    symbol_id: int
    symbol: str
    strategy_id: int
    strategy_name: str
    strategy_version: str
    timeframe: str | None
    confidence: float | None
    reasoning: str
    risks: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecommendationItem:
        return cls(
            symbol_id=int(data["symbol_id"]),
            symbol=str(data.get("symbol", "")),
            strategy_id=int(data["strategy_id"]),
            strategy_name=str(data.get("strategy_name", "")),
            strategy_version=str(data.get("strategy_version", "")),
            timeframe=data.get("timeframe"),
            confidence=data.get("confidence"),
            reasoning=str(data.get("reasoning", "")),
            risks=str(data.get("risks", "")),
        )


class MarketRecommendation:
    """Una consulta de recomendaciones de mercados a la IA."""

    def __init__(
        self,
        id: int | None,
        created_by_user_id: int | None,
        asset_class: str | None,
        summary: str,
        items: list[RecommendationItem],
        market_snapshot: dict[str, Any],
        llm_provider: str | None = None,
        llm_model: str | None = None,
        llm_latency_ms: int | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.created_by_user_id = created_by_user_id
        self.asset_class = asset_class
        self.summary = summary
        self.items = items
        self.market_snapshot = market_snapshot
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_latency_ms = llm_latency_ms
        self.created_at = created_at
