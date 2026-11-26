# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/rest/recommendations/schemas.py
# ======================================================================

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AssetClass = Literal["crypto", "metal", "commodity", "index", "etf", "stock", "forex"]


class GenerateMarketRecommendationsRequest(BaseModel):
    asset_class: AssetClass | None = Field(
        default=None,
        description="Limitar las recomendaciones a una clase de activo; null = todas",
    )
