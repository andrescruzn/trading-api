# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/rest/wallet/routes.py
#
# ENDPOINTS (billetera de la plataforma, fondo común):
# - GET  /wallet            → cuenta, última foto de saldo y estado (staff)
# - PUT  /wallet            → elegir la cuenta que es la billetera (super admin)
# - POST /wallet/sync       → leer el saldo ahora (super admin)
# - GET  /wallet/snapshots  → historia de fotos de saldo (staff)
#
# SEGURIDAD:
# - El inversor nunca ve el saldo total de la billetera: todo es staff.
# - Nunca se devuelven credenciales: de la cuenta solo nombre, exchange_id y modo.
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response, build_success_response
from app.common.security.jwt import staff_required, super_admin_required
from app.extensions.db import get_db
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet
from app.modules.accounts.domain.wallet_snapshot_entity import WalletSnapshot
from app.modules.accounts.providers import AccountServiceFactory
from app.modules.accounts.services.wallet import WalletOverview

from .error_messages import WALLET_ERROR_MESSAGES
from .schemas import SetPlatformWalletRequest

router = APIRouter(prefix="/wallet", tags=["Accounts — Platform wallet"])


def get_factory(db: Session = Depends(get_db)) -> AccountServiceFactory:
    return AccountServiceFactory(session=db)


# ======================================================================
# Serializadores (decimales como texto)
# ======================================================================

def _account_to_dict(a: Account | None) -> dict[str, Any] | None:
    if a is None:
        return None
    return {
        "id":            a.id,
        "name":          a.name,
        "mode":          a.mode,
        "status":        a.status,
        "exchange_id":   a.exchange_id,
    }


def _wallet_to_dict(w: PlatformWallet) -> dict[str, Any]:
    return {
        "account_id":         w.account_id,
        "base_asset":         w.base_asset,
        "last_synced_at":     w.last_synced_at.isoformat() if w.last_synced_at else None,
        "last_sync_error":    w.last_sync_error,
        "last_sync_error_msg": (
            WALLET_ERROR_MESSAGES.get(w.last_sync_error, w.last_sync_error)
            if w.last_sync_error
            else None
        ),
        "updated_by_user_id": w.updated_by_user_id,
        "updated_at":         w.updated_at.isoformat() if w.updated_at else None,
    }


def _snapshot_to_dict(s: WalletSnapshot) -> dict[str, Any]:
    return {
        "id":             s.id,
        "account_id":     s.account_id,
        "base_asset":     s.base_asset,
        "total_value":    str(s.total_value),
        "free_value":     str(s.free_value),
        "locked_value":   str(s.locked_value),
        "source":         s.source,
        "missing_prices": s.missing_prices,
        "assets": [
            {
                "asset":  line.asset,
                "free":   str(line.free),
                "locked": str(line.locked),
                "total":  str(line.total),
                "price":  None if line.price is None else str(line.price),
                "value":  None if line.value is None else str(line.value),
            }
            for line in s.assets
        ],
        "ts": s.ts.isoformat() if s.ts else None,
    }


def _overview_to_dict(o: WalletOverview) -> dict[str, Any]:
    return {
        "configured":      o.wallet is not None,
        "wallet":          _wallet_to_dict(o.wallet) if o.wallet else None,
        "account":         _account_to_dict(o.account),
        "latest_snapshot": _snapshot_to_dict(o.latest_snapshot) if o.latest_snapshot else None,
    }


# ======================================================================
# GET /wallet
# ======================================================================

@router.get("", status_code=200)
def get_wallet(
    _identity: dict = Depends(staff_required),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Billetera de la plataforma y su último saldo (super admin y socio)."""
    result = factory.get_wallet().get()
    return build_success_response(data=_overview_to_dict(result.data))


# ======================================================================
# PUT /wallet
# ======================================================================

@router.put("", status_code=200)
def set_platform_wallet(
    payload: SetPlatformWalletRequest,
    identity: dict = Depends(super_admin_required),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Elige la cuenta de exchange que es la billetera de la plataforma (solo super admin)."""
    result = factory.set_platform_wallet().set(
        account_id=payload.account_id,
        requester_user_id=int(identity["user_id"]),
    )
    if not result.success:
        return build_error_response(result, WALLET_ERROR_MESSAGES)

    overview = factory.get_wallet().get().data
    return build_success_response(
        data=_overview_to_dict(overview),
        msg="Billetera guardada. Sincronízala para ver su saldo.",
    )


# ======================================================================
# POST /wallet/sync
# ======================================================================

@router.post("/sync", status_code=200)
def sync_wallet(
    _identity: dict = Depends(super_admin_required),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Lee el saldo del exchange ahora y guarda la foto (solo super admin)."""
    result = factory.sync_wallet().sync()
    if not result.success:
        return build_error_response(result, WALLET_ERROR_MESSAGES)

    overview = factory.get_wallet().get().data
    return build_success_response(data=_overview_to_dict(overview), msg="Saldo actualizado.")


# ======================================================================
# GET /wallet/snapshots
# ======================================================================

@router.get("/snapshots", status_code=200)
def list_wallet_snapshots(
    limit: int = Query(default=50, ge=1, le=500),
    _identity: dict = Depends(staff_required),
    factory: AccountServiceFactory = Depends(get_factory),
):
    """Fotos de saldo de la billetera, de la más reciente a la más antigua (staff)."""
    result = factory.get_wallet().list_snapshots(limit=limit)
    return build_list_response(items=[_snapshot_to_dict(s) for s in (result.data or [])])
