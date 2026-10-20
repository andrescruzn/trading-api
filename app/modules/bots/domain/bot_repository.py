# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/bot_repository.py
#
# Contrato (interfaz ABC) del repositorio de bots.
# La capa de infrastructure implementa este contrato.
# Los servicios dependen de esta abstracción, no de la implementación.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.modules.bots.domain.bot_entity import Bot
from app.common.contracts import TransactionalRepository


@dataclass(frozen=True)
class BotCriteria:
    """
    Filtros de los listados de bots (mismos en lista simple y paginada).

    `account_ids`: None = sin filtro (todas las cuentas, solo admin);
    [] = ningún bot (usuario sin cuentas): el repositorio no consulta.
    """
    account_ids: list[int] | None = None
    status: str | None = None
    mode: str | None = None


class BotRepository(TransactionalRepository, ABC):

    @abstractmethod
    def get_by_id(self, bot_id: int) -> Bot | None:
        """Obtiene un bot por su ID. Retorna None si no existe."""
        ...

    @abstractmethod
    def list_by_account(self, account_id: int) -> list[Bot]:
        """Lista todos los bots asociados a una cuenta específica."""
        ...

    @abstractmethod
    def list_by_account_ids(self, account_ids: list[int]) -> list[Bot]:
        """Lista los bots de varias cuentas (los de un usuario)."""
        ...

    @abstractmethod
    def list_all(self) -> list[Bot]:
        """Lista todos los bots del sistema (uso admin)."""
        ...

    @abstractmethod
    def search(
        self, criteria: BotCriteria, offset: int = 0, limit: int | None = None
    ) -> list[Bot]:
        """Bots que cumplen `criteria`, el más reciente primero (created_at desc, id desc).
        `limit=None` = sin tope (lista simple)."""
        ...

    @abstractmethod
    def count(self, criteria: BotCriteria) -> int:
        """Total de bots que cumplen `criteria` (paginación)."""
        ...

    @abstractmethod
    def list_by_statuses(self, statuses: list[str]) -> list[Bot]:
        """Lista los bots cuyo status está en `statuses` (uso scheduler)."""
        ...

    @abstractmethod
    def list_shared(self) -> list[Bot]:
        """Lista los bots que comparten sus señales (share_signals = True)."""
        ...

    @abstractmethod
    def create(self, bot: Bot) -> Bot:
        """Persiste un nuevo bot. Retorna la entidad con ID asignado."""
        ...

    @abstractmethod
    def update(self, bot: Bot) -> Bot:
        """Actualiza un bot existente. Lanza ValueError si no existe."""
        ...
