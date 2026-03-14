# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/infrastructure/dataset_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de datasets.
# ======================================================================

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.strategies.domain.dataset_entity import Dataset
from app.modules.strategies.domain.dataset_repository import DatasetRepository
from app.modules.strategies.infrastructure.dataset_model import DatasetModel


class SqlAlchemyDatasetRepository(DatasetRepository):
    """Repositorio concreto de datasets usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mapper
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: DatasetModel) -> Dataset:
        return Dataset(
            id=model.id,
            name=model.name,
            description=model.description,
            symbol_id=model.symbol_id,
            timeframe_id=model.timeframe_id,
            start_ts=model.start_ts,
            end_ts=model.end_ts,
            dataset_hash=model.dataset_hash,
            query_spec=model.query_spec or {},
            created_at=model.created_at,
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        model: Optional[DatasetModel] = self._session.get(DatasetModel, dataset_id)
        return None if model is None else self._to_domain(model)

    def list_all(self) -> list[Dataset]:
        models = (
            self._session.query(DatasetModel)
            .order_by(DatasetModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, dataset: Dataset) -> Dataset:
        model = DatasetModel()
        model.name = dataset.name
        model.description = dataset.description
        model.symbol_id = dataset.symbol_id
        model.timeframe_id = dataset.timeframe_id
        model.start_ts = dataset.start_ts
        model.end_ts = dataset.end_ts
        model.dataset_hash = dataset.dataset_hash
        model.query_spec = dataset.query_spec
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
