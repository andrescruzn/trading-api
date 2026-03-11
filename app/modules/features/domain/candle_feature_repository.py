# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/domain/candle_feature_repository.py
#
# Contrato (interfaz) del repositorio de CandleFeatures.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.modules.features.domain.candle_feature_entity import CandleFeature


class CandleFeatureRepository(ABC):

    @abstractmethod
    def list_features(
        self,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: int,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[CandleFeature]: ...

    @abstractmethod
    def bulk_upsert(self, features: list[CandleFeature]) -> int:
        """Inserta o actualiza features en lote. Retorna filas afectadas."""
        ...
