# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.agent.domain.model_run_entity import ModelRun
from app.modules.agent.domain.model_run_repository import ModelRunRepository


class FinishModelRunService:
    """
    Finaliza una ejecución de entrenamiento.

    - Actualiza el status a 'success' o 'failed'.
    - Registra las métricas obtenidas y el timestamp de finalización.
    """

    def __init__(self, repo: ModelRunRepository, session: Session):
        self._repo = repo
        self._session = session

    def finish(
        self,
        run_id: int,
        status: str,
        metrics: dict[str, Any],
        logs_uri: str | None = None,
    ) -> ServiceResult[ModelRun]:
        run = self._repo.get_by_id(run_id)
        if run is None:
            return ServiceResult.fail(code="MODEL_RUN_NOT_FOUND", http_status=404)

        if not run.is_running():
            return ServiceResult.fail(
                code="MODEL_RUN_ALREADY_FINISHED", http_status=409
            )

        if status not in ("success", "failed"):
            return ServiceResult.fail(
                code="MODEL_RUN_INVALID_STATUS", http_status=422
            )

        run.status = status
        run.metrics = metrics
        run.finished_at = datetime.now(tz=timezone.utc)
        if logs_uri:
            run.logs_uri = logs_uri

        updated = self._repo.update(run)
        self._session.commit()
        return ServiceResult.ok(data=updated)
