# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/signal_subscription_repository.py
#
# Contrato (interfaz ABC) del repositorio de suscripciones a señales.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.common.contracts import TransactionalRepository
from app.modules.bots.domain.signal_subscription_entity import SignalSubscription


class SignalSubscriptionRepository(TransactionalRepository, ABC):

    @abstractmethod
    def list_by_bot(self, bot_id: int) -> list[SignalSubscription]:
        """Suscripciones a un agente (a quién avisar de sus señales)."""
        ...

    @abstractmethod
    def list_bot_ids_by_user(self, user_id: int) -> list[int]:
        """IDs de los agentes que sigue un usuario."""
        ...

    @abstractmethod
    def count_by_bot_ids(self, bot_ids: list[int]) -> dict[int, int]:
        """Número de suscriptores por agente; los que no tienen no aparecen."""
        ...

    @abstractmethod
    def exists(self, bot_id: int, user_id: int) -> bool:
        """True si el usuario ya sigue el agente."""
        ...

    @abstractmethod
    def create(self, subscription: SignalSubscription) -> SignalSubscription:
        """Persiste una suscripción (flush, sin commit)."""
        ...

    @abstractmethod
    def delete(self, bot_id: int, user_id: int) -> bool:
        """Borra la suscripción; True si existía."""
        ...
