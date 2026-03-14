# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.strategies.domain.dataset_entity import Dataset
from app.modules.strategies.domain.dataset_repository import DatasetRepository


class CreateDatasetService:
    """
    Crea un nuevo dataset de backtesting.

    Un dataset referencia un rango de velas + features para un
    símbolo y timeframe. El query_spec define los filtros.
    """

    def __init__(self, repo: DatasetRepository, session: Session):
        self._repo = repo
        self._session = session

    def create(
        self,
        name: str,
        query_spec: dict[str, Any],
        description: str | None = None,
        symbol_id: int | None = None,
        timeframe_id: int | None = None,
        start_ts: datetime | None = None,
        end_ts: datetime | None = None,
    ) -> ServiceResult[Dataset]:
        # Validar rango de fechas si ambas están presentes
        if start_ts and end_ts and end_ts <= start_ts:
            return ServiceResult.fail(code="DATASET_INVALID_DATE_RANGE", http_status=422)

        dataset = Dataset(
            id=0,
            name=name.strip(),
            description=description.strip() if description else None,
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            start_ts=start_ts,
            end_ts=end_ts,
            query_spec=query_spec,
        )

        created = self._repo.create(dataset)
        self._session.commit()
        return ServiceResult.ok(data=created)
