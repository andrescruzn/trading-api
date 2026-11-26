# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/bot_history_repository.py
#
# Contrato (interfaz ABC) del historial de los agentes (`audit_logs`).
#
# NOTAS:
# - `record` no confirma: el evento entra en el mismo commit que el cambio
#   del agente (los repos de un request comparten sesión). Si el cambio se
#   deshace, el evento también.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.common.contracts import Page, PageRequest, TransactionalRepository
from app.modules.bots.domain.bot_history import BotHistoryEntry


class BotHistoryRepository(TransactionalRepository, ABC):

    @abstractmethod
    def record(
        self,
        *,
        bot_id: int,
        event_type: str,
        data: dict[str, Any],
        user_id: int | None = None,
    ) -> None:
        """Añade un evento al historial del agente (sin commit)."""
        ...

    @abstractmethod
    def list_by_bot(self, bot_id: int, page: PageRequest) -> Page[BotHistoryEntry]:
        """Historial del agente, el más reciente primero, con el nombre de quien actuó."""
        ...
