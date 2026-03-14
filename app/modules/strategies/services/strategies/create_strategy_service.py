# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.domain.strategy_repository import StrategyRepository


class CreateStrategyService:
    """
    Crea una nueva estrategia de trading.

    Reglas de negocio:
    - El nombre + versión deben ser únicos.
    - strategy_type debe ser trend_following o mean_reversion.
    - regime_required debe ser coherente con strategy_type:
        · trend_following → trend_up o trend_down (no sideways)
        · mean_reversion  → sideways (no trend_up ni trend_down)
    """

    def __init__(self, repo: StrategyRepository, session: Session):
        self._repo = repo
        self._session = session

    def create(
        self,
        name: str,
        version: str,
        parameters: dict[str, Any],
        description: str | None = None,
    ) -> ServiceResult[Strategy]:
        # Verificar duplicado nombre+versión
        existing = self._repo.get_by_name_version(name, version)
        if existing is not None:
            return ServiceResult.fail(code="STRATEGY_DUPLICATE_NAME_VERSION", http_status=409)

        strategy = Strategy(
            id=0,
            name=name.strip(),
            version=version.strip(),
            description=description.strip() if description else None,
            parameters=parameters,
        )

        # Validar strategy_type
        if not strategy.is_valid_type():
            return ServiceResult.fail(code="STRATEGY_INVALID_TYPE", http_status=422)

        # Validar coherencia tipo ↔ régimen
        if not strategy.is_coherent():
            return ServiceResult.fail(code="STRATEGY_INCOHERENT_REGIME", http_status=422)

        created = self._repo.create(strategy)
        self._session.commit()
        return ServiceResult.ok(data=created)
