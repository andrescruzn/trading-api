# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/domain/candle_feature_entity.py
#
# Entidad de dominio: CandleFeature.
# Representa los indicadores técnicos calculados para una vela concreta.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


class CandleFeature:
    """
    Entidad de dominio: CandleFeature.

    Almacena los valores calculados de todos los indicadores de un
    FeatureSet para una vela (symbol_id + timeframe_id + ts) concreta.
    El campo `features` es un dict JSON con los valores calculados.
    """

    def __init__(
        self,
        id: int,
        symbol_id: int,
        timeframe_id: int,
        ts: datetime,
        feature_set_id: int,
        features: dict[str, Any],
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.symbol_id = symbol_id
        self.timeframe_id = timeframe_id
        self.ts = ts
        self.feature_set_id = feature_set_id
        self.features = features
        self.created_at = created_at
