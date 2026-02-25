# -*- coding: utf-8 -*-

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.market.domain.exchange_entity import Exchange
from app.modules.market.domain.exchange_repository import ExchangeRepository


class CreateExchangeService:
    """Crea un nuevo exchange validando unicidad de nombre y tipo válido."""

    def __init__(self, repo: ExchangeRepository, session: Session):
        self._repo = repo
        self._session = session

    def create(self, name: str, type: str) -> ServiceResult[Exchange]:
        # Validar tipo permitido
        dummy = Exchange(id=0, name=name, type=type)
        if not dummy.is_valid_type():
            return ServiceResult.fail(
                code="EXCHANGE_INVALID_TYPE",
                http_status=422,
            )

        # Verificar unicidad de nombre
        existing = self._repo.get_by_name(name)
        if existing is not None:
            return ServiceResult.fail(
                code="EXCHANGE_NAME_EXISTS",
                http_status=409,
            )

        new_exchange = Exchange(id=0, name=name, type=type, is_active=True)
        created = self._repo.create(new_exchange)
        self._session.commit()

        return ServiceResult.ok(data=created)
