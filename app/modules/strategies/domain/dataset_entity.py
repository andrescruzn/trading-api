# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/domain/dataset_entity.py
#
# Entidad de dominio: Dataset.
# Representa un dataset de backtesting (rango de velas + features).
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any


class Dataset:
    """
    Entidad de dominio: Dataset.

    Un dataset define un conjunto de datos históricos (candles + features)
    para un símbolo y timeframe específicos. Se usa para backtesting
    y entrenamiento de modelos.
    """

    def __init__(
        self,
        id: int,
        name: str,
        query_spec: dict[str, Any],
        description: str | None = None,
        symbol_id: int | None = None,
        timeframe_id: int | None = None,
        start_ts: datetime | None = None,
        end_ts: datetime | None = None,
        dataset_hash: str | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.symbol_id = symbol_id
        self.timeframe_id = timeframe_id
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.dataset_hash = dataset_hash
        self.query_spec = query_spec
        self.created_at = created_at
