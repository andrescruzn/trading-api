# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.strategies.domain.dataset_entity import Dataset
from app.modules.strategies.domain.dataset_repository import DatasetRepository


class GetDatasetService:
    """Obtiene un dataset por su ID."""

    def __init__(self, repo: DatasetRepository):
        self._repo = repo

    def get(self, dataset_id: int) -> ServiceResult[Dataset]:
        dataset = self._repo.get_by_id(dataset_id)
        if dataset is None:
            return ServiceResult.fail(code="DATASET_NOT_FOUND", http_status=404)
        return ServiceResult.ok(data=dataset)
