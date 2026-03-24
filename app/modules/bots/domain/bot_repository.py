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

from app.modules.bots.domain.bot_entity import Bot


class BotRepository(ABC):

    @abstractmethod
    def get_by_id(self, bot_id: int) -> Bot | None:
        """Obtiene un bot por su ID. Retorna None si no existe."""
        ...

    @abstractmethod
    def list_by_account(self, account_id: int) -> list[Bot]:
        """Lista todos los bots asociados a una cuenta específica."""
        ...

    @abstractmethod
    def list_all(self) -> list[Bot]:
        """Lista todos los bots del sistema (uso admin)."""
        ...

    @abstractmethod
    def create(self, bot: Bot) -> Bot:
        """Persiste un nuevo bot. Retorna la entidad con ID asignado."""
        ...

    @abstractmethod
    def update(self, bot: Bot) -> Bot:
        """Actualiza un bot existente. Lanza ValueError si no existe."""
        ...
