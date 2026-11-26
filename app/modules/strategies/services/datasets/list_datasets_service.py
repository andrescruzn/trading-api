# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.strategies.domain.dataset_entity import Dataset
from app.modules.strategies.domain.dataset_repository import DatasetRepository


class ListDatasetsService:
    """Lista todos los datasets disponibles."""

    def __init__(self, repo: DatasetRepository):
        self._repo = repo

    def list(self) -> ServiceResult[list[Dataset]]:
        datasets = self._repo.list_all()
        return ServiceResult.ok(data=datasets)
