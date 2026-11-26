# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/infrastructure/fund_repositories_impl.py
#
# Implementaciones SQLAlchemy de los repositorios del fondo común.
#
# NOTAS:
# - Las fechas de MySQL llegan sin zona: se marcan como UTC al mapear
#   (`ensure_aware_utc`) para compararlas con `utc_now()` y serializarlas
#   con offset.
# - `update_if_status` es un UPDATE condicional: la verificación automática
#   y un super admin pueden intentar resolver la misma solicitud a la vez;
#   solo uno gana y solo ese acredita.
# ======================================================================

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.common.contracts import Page, PageRequest
from app.common.utils import ensure_aware_utc
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.fund.domain.deposit_request_entity import DepositRequest
from app.modules.fund.domain.fund_repositories import (
    DepositRequestRepository,
    FundSettingsRepository,
    LedgerRepository,
)
from app.modules.fund.domain.fund_settings_entity import DepositNetworkConfig, FundSettings
from app.modules.fund.domain.ledger_entry_entity import FundBalances, LedgerEntry
from app.modules.fund.infrastructure.fund_models import (
    DepositRequestModel,
    FundSettingsModel,
    LedgerEntryModel,
)

_SETTINGS_ROW_ID = 1
_ZERO = Decimal("0")


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value)) if value is not None else _ZERO


def _decimal_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


# ======================================================================
# Ajustes
# ======================================================================

class SqlAlchemyFundSettingsRepository(SqlAlchemyRepository, FundSettingsRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: FundSettingsModel) -> FundSettings:
        return FundSettings(
            min_hold_days=int(model.min_hold_days),
            deposit_auto_confirm_max=_decimal(model.deposit_auto_confirm_max),
            deposit_request_ttl_hours=int(model.deposit_request_ttl_hours),
            deposit_networks=[
                DepositNetworkConfig(
                    network=str(item["network"]),
                    name=str(item.get("name") or item["network"]),
                    address=str(item["address"]),
                    tag=item.get("tag") or None,
                )
                for item in (model.deposit_networks or [])
            ],
            updated_by_user_id=model.updated_by_user_id,
            updated_at=ensure_aware_utc(model.updated_at),
        )

    def get(self) -> FundSettings:
        model = self._session.get(FundSettingsModel, _SETTINGS_ROW_ID)
        return FundSettings() if model is None else self._to_domain(model)

    def save(self, settings: FundSettings) -> FundSettings:
        model = self._session.get(FundSettingsModel, _SETTINGS_ROW_ID)
        if model is None:
            model = FundSettingsModel(id=_SETTINGS_ROW_ID)
            self._session.add(model)
        model.min_hold_days = settings.min_hold_days
        model.deposit_auto_confirm_max = settings.deposit_auto_confirm_max
        model.deposit_request_ttl_hours = settings.deposit_request_ttl_hours
        model.deposit_networks = [
            {"network": n.network, "name": n.name, "address": n.address, "tag": n.tag}
            for n in settings.deposit_networks
        ]
        model.updated_by_user_id = settings.updated_by_user_id
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)


# ======================================================================
# Libro mayor
# ======================================================================

class SqlAlchemyLedgerRepository(SqlAlchemyRepository, LedgerRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: LedgerEntryModel) -> LedgerEntry:
        return LedgerEntry(
            id=model.id,
            user_id=model.user_id,
            entry_type=model.entry_type,
            bucket=model.bucket,
            amount=_decimal(model.amount),
            asset=model.asset,
            ref_type=model.ref_type,
            ref_id=model.ref_id,
            bot_id=model.bot_id,
            description=model.description,
            created_by_user_id=model.created_by_user_id,
            created_at=ensure_aware_utc(model.created_at),
        )

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        model = LedgerEntryModel(
            user_id=entry.user_id,
            entry_type=entry.entry_type,
            bucket=entry.bucket,
            amount=entry.amount,
            asset=entry.asset,
            ref_type=entry.ref_type,
            ref_id=entry.ref_id,
            bot_id=entry.bot_id,
            description=entry.description,
            created_by_user_id=entry.created_by_user_id,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def _bucket_sums(self):
        return (
            func.coalesce(
                func.sum(case((LedgerEntryModel.bucket == "pending", LedgerEntryModel.amount), else_=0)),
                0,
            ).label("pending"),
            func.coalesce(
                func.sum(case((LedgerEntryModel.bucket == "available", LedgerEntryModel.amount), else_=0)),
                0,
            ).label("available"),
        )

    def balances_for(self, user_id: int) -> FundBalances:
        pending, available = (
            self._session.query(*self._bucket_sums())
            .filter(LedgerEntryModel.user_id == user_id)
            .one()
        )
        return FundBalances(user_id=int(user_id), pending=_decimal(pending), available=_decimal(available))

    def balances_by_user(self) -> list[FundBalances]:
        rows = (
            self._session.query(LedgerEntryModel.user_id, *self._bucket_sums())
            .group_by(LedgerEntryModel.user_id)
            .order_by(LedgerEntryModel.user_id)
            .all()
        )
        return [
            FundBalances(user_id=int(user_id), pending=_decimal(pending), available=_decimal(available))
            for user_id, pending, available in rows
        ]

    def list_page(self, user_id: int, page: PageRequest) -> Page[LedgerEntry]:
        query = self._session.query(LedgerEntryModel).filter(LedgerEntryModel.user_id == user_id)
        total = query.count()
        models = (
            query.order_by(LedgerEntryModel.created_at.desc(), LedgerEntryModel.id.desc())
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

    def bucket_balance(self, user_id: int, bucket: str) -> Decimal:
        value = (
            self._session.query(func.coalesce(func.sum(LedgerEntryModel.amount), 0))
            .filter(LedgerEntryModel.user_id == user_id, LedgerEntryModel.bucket == bucket)
            .scalar()
        )
        return _decimal(value)

    def total_by_bucket(self) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = defaultdict(lambda: _ZERO)
        rows = (
            self._session.query(LedgerEntryModel.bucket, func.sum(LedgerEntryModel.amount))
            .group_by(LedgerEntryModel.bucket)
            .all()
        )
        for bucket, amount in rows:
            totals[bucket] = _decimal(amount)
        return {"pending": totals["pending"], "available": totals["available"]}


# ======================================================================
# Solicitudes de depósito
# ======================================================================

class SqlAlchemyDepositRequestRepository(SqlAlchemyRepository, DepositRequestRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: DepositRequestModel) -> DepositRequest:
        return DepositRequest(
            id=model.id,
            user_id=model.user_id,
            asset=model.asset,
            network=model.network,
            txid=model.txid,
            declared_amount=_decimal(model.declared_amount),
            status=model.status,
            credited_amount=_decimal_or_none(model.credited_amount),
            address_from=model.address_from,
            exchange_deposit_id=model.exchange_deposit_id,
            exchange_status=model.exchange_status,
            review_reason=model.review_reason,
            resolved_by_user_id=model.resolved_by_user_id,
            resolved_at=ensure_aware_utc(model.resolved_at),
            resolution_note=model.resolution_note,
            expires_at=ensure_aware_utc(model.expires_at),
            created_at=ensure_aware_utc(model.created_at),
            updated_at=ensure_aware_utc(model.updated_at),
        )

    @staticmethod
    def _mutable_fields(request: DepositRequest) -> dict[str, Any]:
        return {
            "status": request.status,
            "credited_amount": request.credited_amount,
            "address_from": request.address_from,
            "exchange_deposit_id": request.exchange_deposit_id,
            "exchange_status": request.exchange_status,
            "review_reason": request.review_reason,
            "resolved_by_user_id": request.resolved_by_user_id,
            "resolved_at": request.resolved_at,
            "resolution_note": request.resolution_note,
        }

    def create(self, request: DepositRequest) -> DepositRequest:
        model = DepositRequestModel(
            user_id=request.user_id,
            asset=request.asset,
            network=request.network,
            txid=request.txid,
            declared_amount=request.declared_amount,
            expires_at=request.expires_at,
            **self._mutable_fields(request),
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, request_id: int) -> DepositRequest | None:
        model = self._session.get(DepositRequestModel, request_id)
        return None if model is None else self._to_domain(model)

    def get_by_txid(self, txid: str) -> DepositRequest | None:
        model = (
            self._session.query(DepositRequestModel)
            .filter(DepositRequestModel.txid == txid)
            .first()
        )
        return None if model is None else self._to_domain(model)

    def txids_in(self, txids: list[str]) -> set[str]:
        if not txids:
            return set()
        rows = (
            self._session.query(DepositRequestModel.txid)
            .filter(DepositRequestModel.txid.in_(txids))
            .all()
        )
        return {row[0] for row in rows}

    def list_by_statuses(self, statuses: list[str]) -> list[DepositRequest]:
        models = (
            self._session.query(DepositRequestModel)
            .filter(DepositRequestModel.status.in_(statuses))
            .order_by(DepositRequestModel.created_at)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def count_open_by_user(self, user_id: int) -> int:
        return (
            self._session.query(func.count(DepositRequestModel.id))
            .filter(
                DepositRequestModel.user_id == user_id,
                DepositRequestModel.status.in_(("pending", "review")),
            )
            .scalar()
            or 0
        )

    def list_page(
        self,
        page: PageRequest,
        user_id: int | None = None,
        statuses: list[str] | None = None,
    ) -> Page[DepositRequest]:
        query = self._session.query(DepositRequestModel)
        if user_id is not None:
            query = query.filter(DepositRequestModel.user_id == user_id)
        if statuses:
            query = query.filter(DepositRequestModel.status.in_(statuses))
        total = query.count()
        models = (
            query.order_by(DepositRequestModel.created_at.desc(), DepositRequestModel.id.desc())
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

    def update_if_status(self, request: DepositRequest, expected: list[str]) -> bool:
        updated = (
            self._session.query(DepositRequestModel)
            .filter(
                DepositRequestModel.id == request.id,
                DepositRequestModel.status.in_(expected),
            )
            .update(self._mutable_fields(request), synchronize_session=False)
        )
        self._session.flush()
        return updated == 1
