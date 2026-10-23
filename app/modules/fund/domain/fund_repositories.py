# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/fund_repositories.py
#
# Contratos de los repositorios del fondo común: ajustes, libro mayor y
# solicitudes de depósito. Implementados en infrastructure/.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.common.contracts import Page, PageRequest, TransactionalRepository
from app.modules.fund.domain.agent_pool_entity import (
    AgentPool,
    AgentSettlement,
    AllocationOrder,
    UnitLot,
)
from app.modules.fund.domain.deposit_request_entity import DepositRequest
from app.modules.fund.domain.fund_settings_entity import FundSettings
from app.modules.fund.domain.ledger_entry_entity import FundBalances, LedgerEntry


class FundSettingsRepository(TransactionalRepository, ABC):

    @abstractmethod
    def get(self) -> FundSettings:
        """Los ajustes guardados, o los valores por defecto si aún no hay fila."""
        ...

    @abstractmethod
    def save(self, settings: FundSettings) -> FundSettings:
        """Crea o reemplaza la única fila (sin commit)."""
        ...


class LedgerRepository(TransactionalRepository, ABC):

    @abstractmethod
    def add(self, entry: LedgerEntry) -> LedgerEntry:
        """Inserta un asiento (append-only, sin commit)."""
        ...

    @abstractmethod
    def balances_for(self, user_id: int) -> FundBalances: ...

    @abstractmethod
    def balances_by_user(self) -> list[FundBalances]:
        """Saldos de cada persona con al menos un asiento."""
        ...

    @abstractmethod
    def list_page(self, user_id: int, page: PageRequest) -> Page[LedgerEntry]:
        """Asientos de una persona, del más reciente al más antiguo."""
        ...

    @abstractmethod
    def bucket_balance(self, user_id: int, bucket: str) -> Decimal:
        """Saldo de una persona en un bucket."""
        ...

    @abstractmethod
    def total_by_bucket(self) -> dict[str, Decimal]:
        """Suma de todo el fondo por bucket (para la conciliación)."""
        ...


class DepositRequestRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, request: DepositRequest) -> DepositRequest: ...

    @abstractmethod
    def get_by_id(self, request_id: int) -> DepositRequest | None: ...

    @abstractmethod
    def get_by_txid(self, txid: str) -> DepositRequest | None: ...

    @abstractmethod
    def txids_in(self, txids: list[str]) -> set[str]:
        """De esos txids, los que ya tienen solicitud (cualquier estado)."""
        ...

    @abstractmethod
    def list_by_statuses(self, statuses: list[str]) -> list[DepositRequest]: ...

    @abstractmethod
    def count_open_by_user(self, user_id: int) -> int: ...

    @abstractmethod
    def list_page(
        self,
        page: PageRequest,
        user_id: int | None = None,
        statuses: list[str] | None = None,
    ) -> Page[DepositRequest]:
        """Del más reciente al más antiguo; `user_id` None = de todos."""
        ...

    @abstractmethod
    def update_if_status(self, request: DepositRequest, expected: list[str]) -> bool:
        """
        Guarda la solicitud solo si su estado en la BD sigue siendo uno de
        `expected` (UPDATE condicional). False = otro proceso la resolvió
        antes: el llamador no debe acreditar nada.
        """
        ...


# ======================================================================
# Capital de los agentes (F4)
# ======================================================================

class AgentPoolRepository(TransactionalRepository, ABC):

    @abstractmethod
    def get_by_id(self, pool_id: int) -> AgentPool | None: ...

    @abstractmethod
    def get_by_bot(self, bot_id: int) -> AgentPool | None: ...

    @abstractmethod
    def list_all(self) -> list[AgentPool]: ...

    @abstractmethod
    def create(self, pool: AgentPool) -> AgentPool: ...

    @abstractmethod
    def update_settled(self, pool: AgentPool, expected_last_fill_id: int) -> bool:
        """
        Guarda equity, unidades y último fill de una liquidación solo si nadie
        liquidó el pool entre medio (su `last_fill_id` sigue siendo el
        esperado). False = otra liquidación ganó: no aplicar nada.
        """
        ...


class UnitLotRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, lot: UnitLot) -> UnitLot: ...

    @abstractmethod
    def list_by_pool(self, pool_id: int) -> list[UnitLot]:
        """Lotes con unidades vivas, del más viejo al más nuevo."""
        ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[UnitLot]:
        """Lotes con unidades vivas de una persona, en todos los agentes."""
        ...


class AllocationOrderRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, order: AllocationOrder) -> AllocationOrder: ...

    @abstractmethod
    def get_by_id(self, order_id: int) -> AllocationOrder | None: ...

    @abstractmethod
    def list_queued(self, pool_id: int | None = None) -> list[AllocationOrder]:
        """En cola (de un agente o de todos), del más viejo al más nuevo."""
        ...

    @abstractmethod
    def queued_total(self, user_id: int, bucket: str) -> Decimal:
        """Lo que una persona ya tiene en cola desde ese bucket."""
        ...

    @abstractmethod
    def update_if_status(self, order: AllocationOrder, expected: list[str]) -> bool:
        """UPDATE condicional por estado (como en los depósitos)."""
        ...


class AgentSettlementRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, settlement: AgentSettlement) -> AgentSettlement: ...

    @abstractmethod
    def list_by_pool(self, pool_id: int, limit: int = 50) -> list[AgentSettlement]:
        """De la más reciente a la más antigua."""
        ...

