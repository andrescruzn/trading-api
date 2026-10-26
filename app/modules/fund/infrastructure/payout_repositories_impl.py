# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/infrastructure/payout_repositories_impl.py
#
# Implementaciones SQLAlchemy de retiros y comisiones (F5). Decimales del
# JSON como texto; fechas marcadas como UTC al leer.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.contracts import Page, PageRequest
from app.common.utils import ensure_aware_utc
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.fund.domain.agent_pool_entity import (
    CommissionCredit,
    RedemptionRequest,
    SettlementRedemption,
)
from app.modules.fund.domain.commission import (
    CommissionShare,
    CommissionShareVersion,
    FeeSchedule,
    FeeTier,
)
from app.modules.fund.domain.payout_repositories import (
    CommissionCreditRepository,
    CommissionShareRepository,
    FeeScheduleRepository,
    PayoutMethodRepository,
    RedemptionRequestRepository,
    SettlementRedemptionRepository,
    WithdrawalReceiptRepository,
    WithdrawalRequestRepository,
)
from app.modules.fund.domain.withdrawal_entity import PayoutMethod, WithdrawalReceipt, WithdrawalRequest
from app.modules.fund.infrastructure.payout_models import (
    CommissionCreditModel,
    CommissionShareVersionModel,
    FeeScheduleModel,
    PayoutMethodModel,
    RedemptionRequestModel,
    SettlementRedemptionModel,
    WithdrawalReceiptModel,
    WithdrawalRequestModel,
)

_ZERO = Decimal("0")


def _dec(value: Any) -> Decimal:
    return Decimal(str(value)) if value is not None else _ZERO


def _dec_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


# ======================================================================
# Tramos y reparto
# ======================================================================

class SqlAlchemyFeeScheduleRepository(SqlAlchemyRepository, FeeScheduleRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: FeeScheduleModel) -> FeeSchedule:
        return FeeSchedule(
            id=m.id,
            tiers=[FeeTier(_dec(t["from_return"]), _dec(t["rate"])) for t in (m.tiers or [])],
            note=m.note,
            created_by_user_id=m.created_by_user_id,
            created_at=ensure_aware_utc(m.created_at),
        )

    def current(self) -> FeeSchedule | None:
        m = self._session.query(FeeScheduleModel).order_by(FeeScheduleModel.id.desc()).first()
        return None if m is None else self._to_domain(m)

    def list_all(self, limit: int = 50) -> list[FeeSchedule]:
        models = (
            self._session.query(FeeScheduleModel).order_by(FeeScheduleModel.id.desc()).limit(limit).all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, schedule: FeeSchedule) -> FeeSchedule:
        m = FeeScheduleModel(
            tiers=[{"from_return": str(t.from_return), "rate": str(t.rate)} for t in schedule.tiers],
            note=schedule.note,
            created_by_user_id=schedule.created_by_user_id,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)


class SqlAlchemyCommissionShareRepository(SqlAlchemyRepository, CommissionShareRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: CommissionShareVersionModel) -> CommissionShareVersion:
        return CommissionShareVersion(
            id=m.id,
            shares=[CommissionShare(int(s["user_id"]), _dec(s["pct"])) for s in (m.shares or [])],
            note=m.note,
            created_by_user_id=m.created_by_user_id,
            created_at=ensure_aware_utc(m.created_at),
        )

    def current(self) -> CommissionShareVersion | None:
        m = (
            self._session.query(CommissionShareVersionModel)
            .order_by(CommissionShareVersionModel.id.desc())
            .first()
        )
        return None if m is None else self._to_domain(m)

    def list_all(self, limit: int = 50) -> list[CommissionShareVersion]:
        models = (
            self._session.query(CommissionShareVersionModel)
            .order_by(CommissionShareVersionModel.id.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, version: CommissionShareVersion) -> CommissionShareVersion:
        m = CommissionShareVersionModel(
            shares=[{"user_id": s.user_id, "pct": str(s.pct)} for s in version.shares],
            note=version.note,
            created_by_user_id=version.created_by_user_id,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)


# ======================================================================
# Salidas de los agentes
# ======================================================================

class SqlAlchemyRedemptionRequestRepository(SqlAlchemyRepository, RedemptionRequestRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: RedemptionRequestModel) -> RedemptionRequest:
        return RedemptionRequest(
            id=m.id,
            pool_id=m.pool_id,
            user_id=m.user_id,
            amount=_dec_or_none(m.amount),
            status=m.status,
            note=m.note,
            settlement_id=m.settlement_id,
            created_by_user_id=m.created_by_user_id,
            created_at=ensure_aware_utc(m.created_at),
            resolved_at=ensure_aware_utc(m.resolved_at),
        )

    def create(self, request: RedemptionRequest) -> RedemptionRequest:
        m = RedemptionRequestModel(
            pool_id=request.pool_id,
            user_id=request.user_id,
            amount=request.amount,
            status=request.status,
            created_by_user_id=request.created_by_user_id,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def get_by_id(self, request_id: int) -> RedemptionRequest | None:
        m = self._session.get(RedemptionRequestModel, request_id)
        return None if m is None else self._to_domain(m)

    def list_queued(self, pool_id: int | None = None) -> list[RedemptionRequest]:
        query = self._session.query(RedemptionRequestModel).filter(
            RedemptionRequestModel.status == "queued"
        )
        if pool_id is not None:
            query = query.filter(RedemptionRequestModel.pool_id == pool_id)
        return [self._to_domain(m) for m in query.order_by(RedemptionRequestModel.id).all()]

    def list_by_user(self, user_id: int, limit: int = 100) -> list[RedemptionRequest]:
        models = (
            self._session.query(RedemptionRequestModel)
            .filter(RedemptionRequestModel.user_id == user_id)
            .order_by(RedemptionRequestModel.id.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def update_if_status(self, request: RedemptionRequest, expected: list[str]) -> bool:
        updated = (
            self._session.query(RedemptionRequestModel)
            .filter(RedemptionRequestModel.id == request.id, RedemptionRequestModel.status.in_(expected))
            .update(
                {
                    "status": request.status,
                    "note": request.note,
                    "settlement_id": request.settlement_id,
                    "resolved_at": request.resolved_at,
                },
                synchronize_session=False,
            )
        )
        self._session.flush()
        return updated == 1


class SqlAlchemySettlementRedemptionRepository(SqlAlchemyRepository, SettlementRedemptionRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: SettlementRedemptionModel) -> SettlementRedemption:
        return SettlementRedemption(
            id=m.id,
            settlement_id=m.settlement_id,
            redemption_request_id=m.redemption_request_id,
            pool_id=m.pool_id,
            user_id=m.user_id,
            units=_dec(m.units),
            value=_dec(m.value),
            cost=_dec(m.cost),
            gain=_dec(m.gain),
            return_pct=_dec(m.return_pct),
            fee=_dec(m.fee),
            net=_dec(m.net),
            pending_amount=_dec_or_none(m.pending_amount),
            fee_schedule_id=m.fee_schedule_id,
            commission_version_id=m.commission_version_id,
            breakdown=list(m.breakdown or []),
            created_at=ensure_aware_utc(m.created_at),
        )

    def create(self, line: SettlementRedemption) -> SettlementRedemption:
        m = SettlementRedemptionModel(
            settlement_id=line.settlement_id,
            redemption_request_id=line.redemption_request_id,
            pool_id=line.pool_id,
            user_id=line.user_id,
            units=line.units,
            value=line.value,
            cost=line.cost,
            gain=line.gain,
            return_pct=line.return_pct,
            fee=line.fee,
            net=line.net,
            pending_amount=line.pending_amount,
            fee_schedule_id=line.fee_schedule_id,
            commission_version_id=line.commission_version_id,
            breakdown=list(line.breakdown),
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def list_by_settlement(self, settlement_id: int) -> list[SettlementRedemption]:
        models = (
            self._session.query(SettlementRedemptionModel)
            .filter(SettlementRedemptionModel.settlement_id == settlement_id)
            .order_by(SettlementRedemptionModel.id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_user(self, user_id: int, limit: int = 100) -> list[SettlementRedemption]:
        models = (
            self._session.query(SettlementRedemptionModel)
            .filter(SettlementRedemptionModel.user_id == user_id)
            .order_by(SettlementRedemptionModel.id.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def totals_by_user(self) -> dict[int, tuple[Decimal, Decimal]]:
        rows = (
            self._session.query(
                SettlementRedemptionModel.user_id,
                func.sum(SettlementRedemptionModel.gain),
                func.sum(SettlementRedemptionModel.fee),
            )
            .group_by(SettlementRedemptionModel.user_id)
            .all()
        )
        return {int(user_id): (_dec(gain), _dec(fee)) for user_id, gain, fee in rows}


class SqlAlchemyCommissionCreditRepository(SqlAlchemyRepository, CommissionCreditRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: CommissionCreditModel) -> CommissionCredit:
        return CommissionCredit(
            id=m.id,
            settlement_redemption_id=m.settlement_redemption_id,
            user_id=m.user_id,
            amount=_dec(m.amount),
            created_at=ensure_aware_utc(m.created_at),
        )

    def create(self, credit: CommissionCredit) -> CommissionCredit:
        m = CommissionCreditModel(
            settlement_redemption_id=credit.settlement_redemption_id,
            user_id=credit.user_id,
            amount=credit.amount,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def list_by_user(self, user_id: int, limit: int = 100) -> list[CommissionCredit]:
        models = (
            self._session.query(CommissionCreditModel)
            .filter(CommissionCreditModel.user_id == user_id)
            .order_by(CommissionCreditModel.id.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def totals_by_user(self) -> dict[int, Decimal]:
        rows = (
            self._session.query(CommissionCreditModel.user_id, func.sum(CommissionCreditModel.amount))
            .group_by(CommissionCreditModel.user_id)
            .all()
        )
        return {int(user_id): _dec(total) for user_id, total in rows}


# ======================================================================
# Medios de pago y retiros
# ======================================================================

class SqlAlchemyPayoutMethodRepository(SqlAlchemyRepository, PayoutMethodRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: PayoutMethodModel) -> PayoutMethod:
        return PayoutMethod(
            id=m.id,
            user_id=m.user_id,
            kind=m.kind,
            label=m.label,
            masked=m.masked,
            usable_from=ensure_aware_utc(m.usable_from),
            is_active=bool(m.is_active),
            created_at=ensure_aware_utc(m.created_at),
        )

    def create(self, method: PayoutMethod, enc_details: str) -> PayoutMethod:
        m = PayoutMethodModel(
            user_id=method.user_id,
            kind=method.kind,
            label=method.label,
            masked=method.masked,
            enc_details=enc_details,
            usable_from=method.usable_from,
            is_active=1,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def get_by_id(self, method_id: int) -> PayoutMethod | None:
        m = self._session.get(PayoutMethodModel, method_id)
        return None if m is None else self._to_domain(m)

    def get_encrypted_details(self, method_id: int) -> str | None:
        m = self._session.get(PayoutMethodModel, method_id)
        return None if m is None else m.enc_details

    def list_by_user(self, user_id: int, only_active: bool = True) -> list[PayoutMethod]:
        query = self._session.query(PayoutMethodModel).filter(PayoutMethodModel.user_id == user_id)
        if only_active:
            query = query.filter(PayoutMethodModel.is_active == 1)
        return [self._to_domain(m) for m in query.order_by(PayoutMethodModel.id.desc()).all()]

    def deactivate(self, method_id: int) -> None:
        self._session.query(PayoutMethodModel).filter(PayoutMethodModel.id == method_id).update(
            {"is_active": 0}, synchronize_session=False
        )
        self._session.flush()


class SqlAlchemyWithdrawalRequestRepository(SqlAlchemyRepository, WithdrawalRequestRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: WithdrawalRequestModel) -> WithdrawalRequest:
        return WithdrawalRequest(
            id=m.id,
            user_id=m.user_id,
            amount=_dec(m.amount),
            payout_method_id=m.payout_method_id,
            status=m.status,
            txid=m.txid,
            network=m.network,
            sent_amount=_dec_or_none(m.sent_amount),
            network_fee=_dec_or_none(m.network_fee),
            exchange_withdrawal_id=m.exchange_withdrawal_id,
            resolution_note=m.resolution_note,
            resolved_by_user_id=m.resolved_by_user_id,
            resolved_at=ensure_aware_utc(m.resolved_at),
            created_at=ensure_aware_utc(m.created_at),
        )

    def create(self, request: WithdrawalRequest) -> WithdrawalRequest:
        m = WithdrawalRequestModel(
            user_id=request.user_id,
            amount=request.amount,
            payout_method_id=request.payout_method_id,
            status=request.status,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def get_by_id(self, request_id: int) -> WithdrawalRequest | None:
        m = self._session.get(WithdrawalRequestModel, request_id)
        return None if m is None else self._to_domain(m)

    def txid_taken(self, txid: str) -> bool:
        return (
            self._session.query(WithdrawalRequestModel.id)
            .filter(WithdrawalRequestModel.txid == txid)
            .first()
            is not None
        )

    def open_summary(self) -> tuple[int, Decimal]:
        count, total = (
            self._session.query(
                func.count(WithdrawalRequestModel.id),
                func.coalesce(func.sum(WithdrawalRequestModel.amount), 0),
            )
            .filter(WithdrawalRequestModel.status == "requested")
            .one()
        )
        return int(count or 0), _dec(total)

    def open_total(self, user_id: int) -> Decimal:
        value = (
            self._session.query(func.coalesce(func.sum(WithdrawalRequestModel.amount), 0))
            .filter(
                WithdrawalRequestModel.user_id == user_id,
                WithdrawalRequestModel.status == "requested",
            )
            .scalar()
        )
        return _dec(value)

    def list_page(
        self,
        page: PageRequest,
        user_id: int | None = None,
        status: str | None = None,
    ) -> Page[WithdrawalRequest]:
        query = self._session.query(WithdrawalRequestModel)
        if user_id is not None:
            query = query.filter(WithdrawalRequestModel.user_id == user_id)
        if status:
            query = query.filter(WithdrawalRequestModel.status == status)
        total = query.count()
        models = (
            query.order_by(WithdrawalRequestModel.created_at.desc(), WithdrawalRequestModel.id.desc())
            .offset(page.offset)
            .limit(page.limit)
            .all()
        )
        return Page(
            items=[self._to_domain(m) for m in models],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    def update_if_status(self, request: WithdrawalRequest, expected: list[str]) -> bool:
        updated = (
            self._session.query(WithdrawalRequestModel)
            .filter(WithdrawalRequestModel.id == request.id, WithdrawalRequestModel.status.in_(expected))
            .update(
                {
                    "status": request.status,
                    "txid": request.txid,
                    "network": request.network,
                    "sent_amount": request.sent_amount,
                    "network_fee": request.network_fee,
                    "exchange_withdrawal_id": request.exchange_withdrawal_id,
                    "resolution_note": request.resolution_note,
                    "resolved_by_user_id": request.resolved_by_user_id,
                    "resolved_at": request.resolved_at,
                },
                synchronize_session=False,
            )
        )
        self._session.flush()
        return updated == 1


class SqlAlchemyWithdrawalReceiptRepository(SqlAlchemyRepository, WithdrawalReceiptRepository):

    def __init__(self, session: Session):
        self._session = session

    def save(self, receipt: WithdrawalReceipt) -> WithdrawalReceipt:
        m = (
            self._session.query(WithdrawalReceiptModel)
            .filter(WithdrawalReceiptModel.withdrawal_request_id == receipt.withdrawal_id)
            .one_or_none()
        )
        if m is None:
            m = WithdrawalReceiptModel(withdrawal_request_id=receipt.withdrawal_id)
            self._session.add(m)
        m.filename = receipt.filename
        m.content_type = receipt.content_type
        m.size_bytes = receipt.size_bytes
        m.content = receipt.content
        m.uploaded_by_user_id = receipt.uploaded_by_user_id
        self._session.flush()
        return receipt

    def get(self, withdrawal_id: int) -> WithdrawalReceipt | None:
        m = (
            self._session.query(WithdrawalReceiptModel)
            .filter(WithdrawalReceiptModel.withdrawal_request_id == withdrawal_id)
            .one_or_none()
        )
        if m is None:
            return None
        return WithdrawalReceipt(
            withdrawal_id=m.withdrawal_request_id,
            filename=m.filename,
            content_type=m.content_type,
            content=bytes(m.content),
            uploaded_by_user_id=m.uploaded_by_user_id,
            created_at=ensure_aware_utc(m.created_at),
        )

    def names_for(self, withdrawal_ids: list[int]) -> dict[int, str]:
        if not withdrawal_ids:
            return {}
        rows = (
            self._session.query(
                WithdrawalReceiptModel.withdrawal_request_id, WithdrawalReceiptModel.filename
            )
            .filter(WithdrawalReceiptModel.withdrawal_request_id.in_(withdrawal_ids))
            .all()
        )
        return {int(wid): name for wid, name in rows}
