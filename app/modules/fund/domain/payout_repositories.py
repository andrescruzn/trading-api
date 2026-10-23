# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/payout_repositories.py
#
# Contratos de los repositorios de retiros y comisiones (F5).
# Implementados en infrastructure/payout_repositories_impl.py.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.common.contracts import Page, PageRequest, TransactionalRepository
from app.modules.fund.domain.agent_pool_entity import (
    CommissionCredit,
    RedemptionRequest,
    SettlementRedemption,
)
from app.modules.fund.domain.commission import CommissionShareVersion, FeeSchedule
from app.modules.fund.domain.withdrawal_entity import (
    PayoutMethod,
    WithdrawalReceipt,
    WithdrawalRequest,
)


class FeeScheduleRepository(TransactionalRepository, ABC):

    @abstractmethod
    def current(self) -> FeeSchedule | None:
        """La versión vigente (la más nueva), o None si nunca se configuró."""
        ...

    @abstractmethod
    def list_all(self, limit: int = 50) -> list[FeeSchedule]: ...

    @abstractmethod
    def create(self, schedule: FeeSchedule) -> FeeSchedule: ...


class CommissionShareRepository(TransactionalRepository, ABC):

    @abstractmethod
    def current(self) -> CommissionShareVersion | None: ...

    @abstractmethod
    def list_all(self, limit: int = 50) -> list[CommissionShareVersion]: ...

    @abstractmethod
    def create(self, version: CommissionShareVersion) -> CommissionShareVersion: ...


class RedemptionRequestRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, request: RedemptionRequest) -> RedemptionRequest: ...

    @abstractmethod
    def get_by_id(self, request_id: int) -> RedemptionRequest | None: ...

    @abstractmethod
    def list_queued(self, pool_id: int | None = None) -> list[RedemptionRequest]: ...

    @abstractmethod
    def list_by_user(self, user_id: int, limit: int = 100) -> list[RedemptionRequest]: ...

    @abstractmethod
    def update_if_status(self, request: RedemptionRequest, expected: list[str]) -> bool: ...


class SettlementRedemptionRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, line: SettlementRedemption) -> SettlementRedemption: ...

    @abstractmethod
    def list_by_settlement(self, settlement_id: int) -> list[SettlementRedemption]: ...

    @abstractmethod
    def list_by_user(self, user_id: int, limit: int = 100) -> list[SettlementRedemption]: ...

    @abstractmethod
    def totals_by_user(self) -> dict[int, tuple[Decimal, Decimal]]:
        """`user_id → (ganancia realizada, comisión pagada)` de todas sus salidas."""
        ...


class CommissionCreditRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, credit: CommissionCredit) -> CommissionCredit: ...

    @abstractmethod
    def list_by_user(self, user_id: int, limit: int = 100) -> list[CommissionCredit]: ...

    @abstractmethod
    def totals_by_user(self) -> dict[int, Decimal]:
        """Comisión acumulada de cada propietario."""
        ...


class PayoutMethodRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, method: PayoutMethod, enc_details: str) -> PayoutMethod: ...

    @abstractmethod
    def get_by_id(self, method_id: int) -> PayoutMethod | None: ...

    @abstractmethod
    def get_encrypted_details(self, method_id: int) -> str | None: ...

    @abstractmethod
    def list_by_user(self, user_id: int, only_active: bool = True) -> list[PayoutMethod]: ...

    @abstractmethod
    def deactivate(self, method_id: int) -> None: ...


class WithdrawalRequestRepository(TransactionalRepository, ABC):

    @abstractmethod
    def create(self, request: WithdrawalRequest) -> WithdrawalRequest: ...

    @abstractmethod
    def get_by_id(self, request_id: int) -> WithdrawalRequest | None: ...

    @abstractmethod
    def open_total(self, user_id: int) -> Decimal:
        """Lo que la persona ya tiene pedido y sin pagar (reservado de su disponible)."""
        ...

    @abstractmethod
    def open_summary(self) -> tuple[int, Decimal]:
        """Retiros por pagar de todo el fondo: (cantidad, total)."""
        ...

    @abstractmethod
    def list_page(
        self,
        page: PageRequest,
        user_id: int | None = None,
        status: str | None = None,
    ) -> Page[WithdrawalRequest]: ...

    @abstractmethod
    def update_if_status(self, request: WithdrawalRequest, expected: list[str]) -> bool: ...


class WithdrawalReceiptRepository(TransactionalRepository, ABC):
    """Un comprobante por retiro; subir otro lo reemplaza."""

    @abstractmethod
    def save(self, receipt: WithdrawalReceipt) -> WithdrawalReceipt: ...

    @abstractmethod
    def get(self, withdrawal_id: int) -> WithdrawalReceipt | None: ...

    @abstractmethod
    def names_for(self, withdrawal_ids: list[int]) -> dict[int, str]:
        """`withdrawal_id → nombre del archivo` sin leer los archivos."""
        ...
