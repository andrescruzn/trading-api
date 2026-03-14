# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.domain.strategy_repository import StrategyRepository


class UpdateStrategyService:
    """
    Actualiza una estrategia existente.

    Reglas de negocio:
    - La estrategia debe existir.
    - Si se cambia nombre/versión, no debe colisionar con otra existente.
    - Se re-valida coherencia strategy_type ↔ regime_required.
    """

    def __init__(self, repo: StrategyRepository, session: Session):
        self._repo = repo
        self._session = session

    def update(
        self,
        strategy_id: int,
        name: str | None = None,
        version: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> ServiceResult[Strategy]:
        strategy = self._repo.get_by_id(strategy_id)
        if strategy is None:
            return ServiceResult.fail(code="STRATEGY_NOT_FOUND", http_status=404)

        # Aplicar cambios
        if name is not None:
            strategy.name = name.strip()
        if version is not None:
            strategy.version = version.strip()
        if description is not None:
            strategy.description = description.strip()
        if parameters is not None:
            strategy.parameters = parameters

        # Verificar colisión de nombre+versión (excluyendo a sí mismo)
        collision = self._repo.get_by_name_version(strategy.name, strategy.version)
        if collision is not None and collision.id != strategy_id:
            return ServiceResult.fail(code="STRATEGY_DUPLICATE_NAME_VERSION", http_status=409)

        # Revalidar tipo y coherencia
        if not strategy.is_valid_type():
            return ServiceResult.fail(code="STRATEGY_INVALID_TYPE", http_status=422)

        if not strategy.is_coherent():
            return ServiceResult.fail(code="STRATEGY_INCOHERENT_REGIME", http_status=422)

        updated = self._repo.update(strategy)
        self._session.commit()
        return ServiceResult.ok(data=updated)
