# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/overview/fund_overview_service.py
#
# CASO DE USO:
# - overview() → el resumen del fondo para los propietarios (staff):
#   billetera, capital de cada agente, saldos de las personas, retiros por
#   pagar, depósitos por resolver, la CONCILIACIÓN y lo que ganó cada
#   propietario o socio.
# - summary(user_id) → lo que ganó una persona (Mi saldo, cualquier rol).
#
# CONCILIACIÓN (cada peso de la billetera tiene dueño):
#   diferencia = total de la billetera
#                − capital de los agentes (equity liquidada + resultado
#                  desde entonces, lo abierto a costo)
#                − pendiente de asignar − disponible de todas las personas
# Lo esperado es ≈ 0. Positiva: depósitos aún sin acreditar o sin reclamar,
# posiciones abiertas que valen más que su costo, redondeos. Negativa:
# posiciones que valen menos que su costo, comisiones en otra moneda o
# dinero que salió de la billetera por fuera del fondo: hay que revisarla.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.platform_wallet_repository import (
    PlatformWalletRepository,
    WalletSnapshotRepository,
)
from app.modules.accounts.domain.wallet_snapshot_entity import WalletSnapshot
from app.modules.fund.domain.fund_repositories import (
    AllocationOrderRepository,
    DepositRequestRepository,
    LedgerRepository,
)
from app.modules.fund.domain.payout_repositories import (
    CommissionCreditRepository,
    SettlementRedemptionRepository,
    WithdrawalRequestRepository,
)
from app.modules.fund.services.pools.agent_pools_service import AgentPoolsService, PoolOverview
from app.modules.fund.services.pools.participations_service import ParticipationsService
from app.modules.users.domain.user_repository import UserRepository

_ZERO = Decimal("0")


@dataclass(frozen=True)
class ParticipantSummary:
    """Lo que ganó una persona: comisiones recibidas + su dinero como inversor."""

    user_id: int
    commissions: Decimal
    realized_gain: Decimal
    fees_paid: Decimal
    in_agents_cost: Decimal
    in_agents_value: Decimal
    pending: Decimal
    available: Decimal

    @property
    def unrealized_gain(self) -> Decimal:
        return self.in_agents_value - self.in_agents_cost

    @property
    def total_earned(self) -> Decimal:
        # Comisión recibida + ganancia neta como inversor (realizada y no)
        return self.commissions + self.realized_gain - self.fees_paid + self.unrealized_gain


@dataclass(frozen=True)
class FundOverview:
    asset: str
    snapshot: WalletSnapshot | None
    last_synced_at: datetime | None
    last_sync_error: str | None
    agents: list[PoolOverview]
    agents_capital: Decimal
    pending_total: Decimal
    available_total: Decimal
    queued_allocations: Decimal
    open_withdrawals_count: int
    open_withdrawals_total: Decimal
    deposits_waiting_count: int
    deposits_waiting_total: Decimal
    owners: list[ParticipantSummary] = field(default_factory=list)

    @property
    def accounted(self) -> Decimal:
        return self.agents_capital + self.pending_total + self.available_total

    @property
    def difference(self) -> Decimal | None:
        """None sin foto de la billetera (no se puede conciliar)."""
        return None if self.snapshot is None else self.snapshot.total_value - self.accounted


class FundOverviewService:

    def __init__(
        self,
        *,
        wallet_repo: PlatformWalletRepository,
        snapshot_repo: WalletSnapshotRepository,
        pools: AgentPoolsService,
        participations: ParticipationsService,
        ledger_repo: LedgerRepository,
        allocation_repo: AllocationOrderRepository,
        deposit_repo: DepositRequestRepository,
        withdrawal_repo: WithdrawalRequestRepository,
        line_repo: SettlementRedemptionRepository,
        credit_repo: CommissionCreditRepository,
        user_repo: UserRepository,
        staff_role_ids: tuple[int, ...],
        asset: str,
    ):
        self._wallet_repo = wallet_repo
        self._snapshot_repo = snapshot_repo
        self._pools = pools
        self._participations = participations
        self._ledger_repo = ledger_repo
        self._allocation_repo = allocation_repo
        self._deposit_repo = deposit_repo
        self._withdrawal_repo = withdrawal_repo
        self._line_repo = line_repo
        self._credit_repo = credit_repo
        self._user_repo = user_repo
        self._staff_role_ids = staff_role_ids
        self._asset = asset.upper()

    def overview(self) -> ServiceResult[FundOverview]:
        wallet = self._wallet_repo.get()
        snapshot = self._snapshot_repo.get_latest(wallet.account_id) if wallet else None

        agents = self._pools.list().data or []
        buckets = self._ledger_repo.total_by_bucket()
        withdrawals_count, withdrawals_total = self._withdrawal_repo.open_summary()
        waiting = self._deposit_repo.list_by_statuses(["pending", "review"])

        return ServiceResult.ok(
            FundOverview(
                asset=wallet.base_asset if wallet else self._asset,
                snapshot=snapshot,
                last_synced_at=wallet.last_synced_at if wallet else None,
                last_sync_error=wallet.last_sync_error if wallet else None,
                agents=agents,
                agents_capital=sum((a.estimated_capital for a in agents), _ZERO),
                pending_total=buckets.get("pending", _ZERO),
                available_total=buckets.get("available", _ZERO),
                queued_allocations=sum(
                    (o.amount for o in self._allocation_repo.list_queued()), _ZERO
                ),
                open_withdrawals_count=withdrawals_count,
                open_withdrawals_total=withdrawals_total,
                deposits_waiting_count=len(waiting),
                deposits_waiting_total=sum(
                    (r.credited_amount or r.declared_amount for r in waiting), _ZERO
                ),
                owners=self._owners(),
            )
        )

    def summary(self, user_id: int) -> ServiceResult[ParticipantSummary]:
        return ServiceResult.ok(
            self._summary(
                int(user_id),
                commissions=self._credit_repo.totals_by_user(),
                realized=self._line_repo.totals_by_user(),
                balances={int(user_id): self._ledger_repo.balances_for(int(user_id))},
            )
        )

    def _owners(self) -> list[ParticipantSummary]:
        staff = [
            u for u in self._user_repo.list_all()
            if u.role_id in self._staff_role_ids and u.status == "active"
        ]
        commissions = self._credit_repo.totals_by_user()
        realized = self._line_repo.totals_by_user()
        balances = {b.user_id: b for b in self._ledger_repo.balances_by_user()}
        owners = [
            self._summary(u.id, commissions=commissions, realized=realized, balances=balances)
            for u in staff
        ]
        owners.sort(key=lambda o: o.total_earned, reverse=True)
        return owners

    def _summary(
        self,
        user_id: int,
        *,
        commissions: dict[int, Decimal],
        realized: dict[int, tuple[Decimal, Decimal]],
        balances: dict,
    ) -> ParticipantSummary:
        cost: Decimal = _ZERO
        value: Decimal = _ZERO
        for participation in self._participations.mine(user_id).data or []:
            cost += participation.cost
            value += participation.value
        gain, fees = realized.get(user_id, (_ZERO, _ZERO))
        balance = balances.get(user_id)
        return ParticipantSummary(
            user_id=user_id,
            commissions=commissions.get(user_id, _ZERO),
            realized_gain=gain,
            fees_paid=fees,
            in_agents_cost=cost,
            in_agents_value=value,
            pending=balance.pending if balance else _ZERO,
            available=balance.available if balance else _ZERO,
        )
