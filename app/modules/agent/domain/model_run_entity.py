# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/domain/model_run_entity.py
#
# Entidad de dominio: ModelRun.
# Representa una ejecución de entrenamiento de un modelo ML.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any


class ModelRun:
    """
    Entidad de dominio: ModelRun.

    Registra cada ciclo de entrenamiento de un modelo ML:
    cuándo empezó, cuándo terminó, con qué parámetros y qué métricas obtuvo.

    Estados válidos:
    - running : entrenamiento en progreso
    - success : entrenamiento completado con éxito
    - failed  : entrenamiento terminó con error
    """

    VALID_STATUSES = ("running", "success", "failed")

    def __init__(
        self,
        id: int,
        model_id: int,
        metrics: dict[str, Any],
        params: dict[str, Any],
        dataset_id: int | None = None,
        status: str = "running",
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        logs_uri: str | None = None,
    ):
        self.id = id
        self.model_id = model_id
        self.dataset_id = dataset_id
        self.status = status
        self.metrics = metrics
        self.params = params
        self.logs_uri = logs_uri
        self.started_at = started_at
        self.finished_at = finished_at

    # ------------------------------------------------------------------
    # Validaciones de negocio
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        return self.status == "running"

    def is_finished(self) -> bool:
        return self.status in ("success", "failed")
