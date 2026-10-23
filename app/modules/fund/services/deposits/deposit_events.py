# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/deposits/deposit_events.py
#
# Eventos de aviso de los depósitos (los usan verificar, resolver y
# asignar los sin reclamar). Los textos están en el módulo alerts.
# ======================================================================

from __future__ import annotations

from app.modules.fund.domain.deposit_request_entity import DepositRequest
from app.modules.fund.domain.fund_notifier import (
    FUND_DEPOSIT_CONFIRMED,
    FUND_DEPOSIT_IN_REVIEW,
    FUND_DEPOSIT_REJECTED,
    FundEvent,
)


def confirmed_event(request: DepositRequest) -> FundEvent:
    amount = request.credited_amount if request.credited_amount is not None else request.declared_amount
    return FundEvent(
        code=FUND_DEPOSIT_CONFIRMED,
        user_id=request.user_id,
        data={"amount": str(amount), "asset": request.asset},
    )


def rejected_event(request: DepositRequest) -> FundEvent:
    return FundEvent(
        code=FUND_DEPOSIT_REJECTED,
        user_id=request.user_id,
        data={
            "amount": str(request.declared_amount),
            "asset": request.asset,
            "note": request.resolution_note or "—",
        },
    )


def review_event(request: DepositRequest) -> FundEvent:
    """A los super admin: un depósito espera su decisión."""
    return FundEvent(
        code=FUND_DEPOSIT_IN_REVIEW,
        about_user_id=request.user_id,
        data={
            "amount": str(request.credited_amount or request.declared_amount),
            "asset": request.asset,
            "reason": request.review_reason or "",
        },
    )
