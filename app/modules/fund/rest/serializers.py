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
