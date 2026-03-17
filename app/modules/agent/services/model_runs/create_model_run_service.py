# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.agent.domain.model_run_entity import ModelRun
from app.modules.agent.domain.model_run_repository import ModelRunRepository
from app.modules.agent.domain.ml_model_repository import MLModelRepository


class CreateModelRunService:
    """
    Inicia una nueva ejecución de entrenamiento para un modelo.

    Reglas:
    - El modelo debe existir.
    - El run se crea en status 'running'.
    """

    def __init__(
        self,
        run_repo: ModelRunRepository,
        model_repo: MLModelRepository,
        session: Session,
    ):
        self._run_repo = run_repo
        self._model_repo = model_repo
        self._session = session

    def create(
        self,
        model_id: int,
        params: dict[str, Any],
        dataset_id: Optional[int] = None,
        logs_uri: Optional[str] = None,
    ) -> ServiceResult[ModelRun]:
        # Verificar que el modelo existe
        model = self._model_repo.get_by_id(model_id)
        if model is None:
            return ServiceResult.fail(code="MODEL_NOT_FOUND", http_status=404)

        run = ModelRun(
            id=0,
            model_id=model_id,
            dataset_id=dataset_id,
            status="running",
            metrics={},
            params=params,
            logs_uri=logs_uri,
        )

        created = self._run_repo.create(run)
        self._session.commit()
        return ServiceResult.ok(data=created)
