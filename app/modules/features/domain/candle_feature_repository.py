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
from app.common.contracts import TransactionalRepository


class CandleFeatureRepository(TransactionalRepository, ABC):

    @abstractmethod
    def list_features(
        self,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: Optional[int] = None,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[CandleFeature]: ...

    @abstractmethod
    def bulk_upsert(self, features: list[CandleFeature]) -> int:
        """Inserta o actualiza features en lote. Retorna filas afectadas."""
        ...

    @abstractmethod
    def delete_beyond_retention(
        self,
        symbol_id: int,
        timeframe_id: int,
        feature_set_id: int,
        retention: int,
    ) -> int:
        """Borra las features más antiguas que las últimas `retention` de la tripla."""
        ...
