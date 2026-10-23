# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/serializers.py
#
# Entidades del fondo → dict para la API (decimales como texto, fechas ISO
# con zona). Compartido por las rutas de ajustes, depósitos y libro.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.modules.accounts.domain.wallet_gateway import DepositNetwork, ExchangeDeposit
from app.modules.fund.domain import (
    DepositNetworkConfig,
    DepositRequest,
    FundBalances,
    FundSettings,
    LedgerEntry,
)
from app.modules.fund.domain.agent_pool_entity import (
    AgentSettlement,
    AllocationOrder,
    CommissionCredit,
    RedemptionRequest,
    SettlementRedemption,
)
from app.modules.fund.domain.commission import CommissionShareVersion, FeeSchedule, TierCharge
from app.modules.fund.domain.withdrawal_entity import PayoutMethod, WithdrawalRequest
from app.modules.fund.services.fees import OwnerEarning
from app.modules.fund.services.pools import (
    AgentInfo,
    ParticipantPosition,
    Participation,
    PoolDetail,
    PoolOverview,
    SettlementPreview,
)
from app.modules.fund.services.settings import DepositInfo


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _money(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def network_config_to_dict(n: DepositNetworkConfig) -> dict[str, Any]:
    return {"network": n.network, "name": n.name, "address": n.address, "tag": n.tag}


def settings_to_dict(s: FundSettings) -> dict[str, Any]:
    return {
        "min_hold_days":             s.min_hold_days,
        "deposit_auto_confirm_max":  _money(s.deposit_auto_confirm_max),
        "deposit_request_ttl_hours": s.deposit_request_ttl_hours,
        "deposit_networks":          [network_config_to_dict(n) for n in s.deposit_networks],
        "updated_by_user_id":        s.updated_by_user_id,
        "updated_at":                _iso(s.updated_at),
    }


def deposit_info_to_dict(info: DepositInfo) -> dict[str, Any]:
    return {
        "enabled":           info.enabled,
        "asset":             info.asset,
        "networks":          [network_config_to_dict(n) for n in info.networks],
        "min_hold_days":     info.min_hold_days,
        "request_ttl_hours": info.request_ttl_hours,
    }


def available_network_to_dict(n: DepositNetwork) -> dict[str, Any]:
    return {"code": n.code, "name": n.name, "deposit_enabled": n.deposit_enabled}


def deposit_request_to_dict(r: DepositRequest) -> dict[str, Any]:
    return {
        "id":                  r.id,
        "user_id":             r.user_id,
        "asset":               r.asset,
        "network":             r.network,
        "txid":                r.txid,
        "declared_amount":     _money(r.declared_amount),
        "credited_amount":     _money(r.credited_amount),
        "address_from":        r.address_from,
        "exchange_status":     r.exchange_status,
        "status":              r.status,
        "review_reason":       r.review_reason,
        "resolved_by_user_id": r.resolved_by_user_id,
        "resolved_at":         _iso(r.resolved_at),
        "resolution_note":     r.resolution_note,
        "expires_at":          _iso(r.expires_at),
        "created_at":          _iso(r.created_at),
    }


def exchange_deposit_to_dict(d: ExchangeDeposit) -> dict[str, Any]:
    return {
        "txid":         d.txid,
        "amount":       _money(d.amount),
        "asset":        d.asset,
        "network":      d.network,
        "status":       d.status,
        "address_from": d.address_from,
        "ts":           _iso(d.ts),
    }


def balances_to_dict(b: FundBalances) -> dict[str, Any]:
    return {
        "user_id":   b.user_id,
        "pending":   _money(b.pending),
        "available": _money(b.available),
        "total":     _money(b.total),
    }


def ledger_entry_to_dict(e: LedgerEntry) -> dict[str, Any]:
    return {
        "id":                 e.id,
        "user_id":            e.user_id,
        "entry_type":         e.entry_type,
        "bucket":             e.bucket,
        "amount":             _money(e.amount),
        "asset":              e.asset,
        "ref_type":           e.ref_type,
        "ref_id":             e.ref_id,
        "bot_id":             e.bot_id,
        "description":        e.description,
        "created_by_user_id": e.created_by_user_id,
        "created_at":         _iso(e.created_at),
    }


# ======================================================================
# Agentes del fondo (F4)
# ======================================================================

def agent_info_to_dict(a: AgentInfo | None) -> dict[str, Any] | None:
    if a is None:
        return None
    return {"bot_id": a.bot_id, "name": a.name, "status": a.status, "mode": a.mode, "symbol": a.symbol}


def pool_overview_to_dict(o: PoolOverview) -> dict[str, Any]:
    p = o.pool
    return {
        "id":                p.id,
        "bot_id":            p.bot_id,
        "asset":             p.asset,
        "equity":            _money(p.equity),
        "units":             _money(p.units),
        "nav":               _money(p.nav),
        "estimated_capital": _money(o.estimated_capital),
        "queued_total":      _money(o.queued_total),
        "participants":      o.participants,
        "last_settled_at":   _iso(o.last_settled_at),
        "created_at":        _iso(p.created_at),
        "agent":             agent_info_to_dict(o.agent),
    }


def allocation_to_dict(a: AllocationOrder) -> dict[str, Any]:
    return {
        "id":                 a.id,
        "pool_id":            a.pool_id,
        "user_id":            a.user_id,
        "amount":             _money(a.amount),
        "source_bucket":      a.source_bucket,
        "status":             a.status,
        "note":               a.note,
        "settlement_id":      a.settlement_id,
        "created_by_user_id": a.created_by_user_id,
        "created_at":         _iso(a.created_at),
        "resolved_at":        _iso(a.resolved_at),
    }


def settlement_to_dict(s: AgentSettlement) -> dict[str, Any]:
    return {
        "id":                 s.id,
        "pool_id":            s.pool_id,
        "previous_equity":    _money(s.previous_equity),
        "trading_result":     _money(s.trading_result),
        "equity_before":      _money(s.equity_before),
        "units_before":       _money(s.units_before),
        "nav":                _money(s.nav),
        "allocated_amount":   _money(s.allocated_amount),
        "units_issued":       _money(s.units_issued),
        "equity_after":       _money(s.equity_after),
        "units_after":        _money(s.units_after),
        "fills_count":        s.fills_count,
        "unvalued_fees":      s.unvalued_fees,
        "note":               s.note,
        "created_by_user_id": s.created_by_user_id,
        "settled_at":         _iso(s.settled_at),
        "redeemed_amount":    _money(s.redeemed_amount),
        "units_redeemed":     _money(s.units_redeemed),
        "fees_total":         _money(s.fees_total),
    }


def participant_to_dict(p: ParticipantPosition) -> dict[str, Any]:
    return {
        "user_id":           p.user_id,
        "units":             _money(p.units),
        "cost":              _money(p.cost),
        "value":             _money(p.value),
        "share":             _money(p.share),
        "first_acquired_at": _iso(p.first_acquired_at),
    }


def pool_detail_to_dict(d: PoolDetail) -> dict[str, Any]:
    return {
        **pool_overview_to_dict(d.overview),
        "participants_detail": [participant_to_dict(p) for p in d.participants],
        "queued":              [allocation_to_dict(a) for a in d.queued],
        "settlements":         [settlement_to_dict(s) for s in d.settlements],
        "queued_redemptions":  [redemption_request_to_dict(r) for r in d.queued_redemptions],
    }


def settlement_preview_to_dict(p: SettlementPreview) -> dict[str, Any]:
    plan = p.plan
    return {
        "pool_id":          p.pool.id,
        "blockers":         p.blockers,
        "fills_count":      p.flow.fills_count,
        "sells":            _money(p.flow.sells),
        "buys":             _money(p.flow.buys),
        "fees":             _money(p.flow.fees),
        "unvalued_fees":    {k: str(v) for k, v in p.flow.unvalued_fees.items()},
        "previous_equity":  _money(plan.previous_equity),
        "trading_result":   _money(plan.trading_result),
        "equity_before":    _money(plan.equity_before),
        "units_before":     _money(plan.units_before),
        "nav":              _money(plan.nav),
        "allocations": [
            {**allocation_to_dict(a.order), "units": _money(a.units)} for a in plan.allocations
        ],
        "canceled": [
            {**allocation_to_dict(c.order), "reason": c.reason} for c in plan.canceled
        ],
        "allocated_amount": _money(plan.allocated_amount),
        "units_issued":     _money(plan.units_issued),
        "equity_after":     _money(plan.equity_after),
        "units_after":      _money(plan.units_after),
        # F5: salidas
        "redemptions": [
            {
                **redemption_request_to_dict(r.order),
                "units":          _money(r.units),
                "value":          _money(r.value),
                "cost":           _money(r.cost),
                "gain":           _money(r.gain),
                "return_pct":     _money(r.return_pct),
                "fee":            _money(r.fee),
                "net":            _money(r.net),
                "pending_amount": _money(r.pending_amount),
                "breakdown":      [tier_charge_to_dict(c) for c in r.breakdown],
                "commissions":    [{"user_id": u, "amount": _money(a)} for u, a in r.commissions],
            }
            for r in plan.redemptions
        ],
        "waiting_redemptions": [redemption_request_to_dict(r) for r in plan.waiting_redemptions],
        "redeemed_amount":  _money(plan.redeemed_amount),
        "fees_total":       _money(plan.fees_total),
        "hold_cutoff":      _iso(p.hold_cutoff),
        "fee_schedule_id":  p.fee_schedule.id if p.fee_schedule else None,
        "commission_version_id": p.shares.id if p.shares else None,
    }


def participation_to_dict(p: Participation) -> dict[str, Any]:
    return {
        "pool_id":           p.pool_id,
        "agent":             agent_info_to_dict(p.agent),
        "units":             _money(p.units),
        "cost":              _money(p.cost),
        "nav":               _money(p.nav),
        "value":             _money(p.value),
        "result":            _money(p.result),
        "first_acquired_at": _iso(p.first_acquired_at),
        "last_settled_at":   _iso(p.last_settled_at),
    }


# ======================================================================
# Salidas, comisiones y retiros (F5); porcentajes también en %
# ======================================================================

def _pct(value: Decimal | None) -> str | None:
    return None if value is None else str((value * 100).normalize())


def tier_charge_to_dict(c: TierCharge) -> dict[str, Any]:
    return {
        "from_return_pct": _pct(c.from_return),
        "to_return_pct":   _pct(c.to_return),
        "rate_pct":        _pct(c.rate),
        "base":            _money(c.base),
        "fee":             _money(c.fee),
    }


def fee_schedule_to_dict(f: FeeSchedule) -> dict[str, Any]:
    return {
        "id":    f.id,
        "tiers": [{"from_return_pct": _pct(t.from_return), "rate_pct": _pct(t.rate)} for t in f.tiers],
        "note":  f.note,
        "created_by_user_id": f.created_by_user_id,
        "created_at": _iso(f.created_at),
    }


def commission_shares_to_dict(v: CommissionShareVersion) -> dict[str, Any]:
    return {
        "id":     v.id,
        "shares": [{"user_id": s.user_id, "pct": _pct(s.pct)} for s in v.shares],
        "note":   v.note,
        "created_by_user_id": v.created_by_user_id,
        "created_at": _iso(v.created_at),
    }


def owner_earning_to_dict(e: OwnerEarning) -> dict[str, Any]:
    return {"user_id": e.user_id, "commissions": _money(e.commissions)}


def commission_credit_to_dict(c: CommissionCredit) -> dict[str, Any]:
    return {
        "id":                       c.id,
        "settlement_redemption_id": c.settlement_redemption_id,
        "amount":                   _money(c.amount),
        "created_at":               _iso(c.created_at),
    }


def redemption_request_to_dict(r: RedemptionRequest) -> dict[str, Any]:
    return {
        "id":            r.id,
        "pool_id":       r.pool_id,
        "user_id":       r.user_id,
        "amount":        _money(r.amount),
        "status":        r.status,
        "note":          r.note,
        "settlement_id": r.settlement_id,
        "created_at":    _iso(r.created_at),
        "resolved_at":   _iso(r.resolved_at),
    }


def settlement_redemption_to_dict(line: SettlementRedemption) -> dict[str, Any]:
    return {
        "id":                    line.id,
        "settlement_id":         line.settlement_id,
        "redemption_request_id": line.redemption_request_id,
        "pool_id":               line.pool_id,
        "units":                 _money(line.units),
        "value":                 _money(line.value),
        "cost":                  _money(line.cost),
        "gain":                  _money(line.gain),
        "return_pct":            _pct(line.return_pct),
        "fee":                   _money(line.fee),
        "net":                   _money(line.net),
        "pending_amount":        _money(line.pending_amount),
        "breakdown": [
            {
                "from_return_pct": _pct(_dec_or_none(b.get("from_return"))),
                "to_return_pct":   _pct(_dec_or_none(b.get("to_return"))),
                "rate_pct":        _pct(_dec_or_none(b.get("rate"))),
                "base":            b.get("base"),
                "fee":             b.get("fee"),
            }
            for b in line.breakdown
        ],
        "created_at": _iso(line.created_at),
    }


def _dec_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def payout_method_to_dict(m: PayoutMethod, *, with_details: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id":          m.id,
        "user_id":     m.user_id,
        "kind":        m.kind,
        "label":       m.label,
        "masked":      m.masked,
        "usable_from": _iso(m.usable_from),
        "is_active":   m.is_active,
        "created_at":  _iso(m.created_at),
    }
    if with_details:
        data["details"] = dict(m.details)
    return data


def withdrawal_to_dict(w: WithdrawalRequest) -> dict[str, Any]:
    return {
        "id":                  w.id,
        "user_id":             w.user_id,
        "amount":              _money(w.amount),
        "payout_method_id":    w.payout_method_id,
        "status":              w.status,
        "paid_cop_amount":     _money(w.paid_cop_amount),
        "cop_rate":            _money(w.cop_rate),
        "payment_reference":   w.payment_reference,
        "resolution_note":     w.resolution_note,
        "resolved_by_user_id": w.resolved_by_user_id,
        "resolved_at":         _iso(w.resolved_at),
        "created_at":          _iso(w.created_at),
    }

