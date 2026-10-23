# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/pools/routes.py
#
# ENDPOINTS (agentes del fondo común, F4):
# - GET  /fund/agents                          → pools con su agente y resumen (staff)
# - GET  /fund/agents/eligible                 → agentes que se pueden abrir (super admin)
# - POST /fund/agents                          → abrir un agente al fondo (super admin)
# - GET  /fund/agents/{pool_id}                → detalle: participantes, cola, liquidaciones (staff)
# - POST /fund/agents/{pool_id}/allocations    → encolar una asignación (super admin)
# - POST /fund/allocations/{id}/cancel         → sacar una asignación de la cola (super admin)
# - GET  /fund/agents/{pool_id}/settlement-preview → liquidación calculada, sin escribir (staff)
# - POST /fund/agents/{pool_id}/settle         → liquidar (super admin)
# - GET  /fund/me/participations               → en qué agentes está mi dinero (con sesión)
# - POST /fund/redemptions                     → pedir salida de un agente (la persona o un super admin)
# - POST /fund/redemptions/{id}/cancel         → anular una salida en cola
# - GET  /fund/me/redemptions                  → mis salidas: en cola, historial y lo que salió
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_success_response,
)
from app.common.security.jwt import (
    is_super_admin,
    staff_required,
    super_admin_required,
    token_required_actual,
)
from app.extensions.db import get_db
from app.modules.fund.providers import FundServiceFactory
from app.modules.fund.rest.error_messages import FUND_ERROR_MESSAGES
from app.modules.fund.rest.schemas import (
    OpenPoolRequest,
    QueueAllocationRequest,
    RedemptionCreateRequest,
    SettleRequest,
)
from app.modules.fund.rest.serializers import (
    agent_info_to_dict,
    allocation_to_dict,
    participation_to_dict,
    pool_detail_to_dict,
    pool_overview_to_dict,
    redemption_request_to_dict,
    settlement_preview_to_dict,
    settlement_redemption_to_dict,
    settlement_to_dict,
)

router = APIRouter(prefix="/fund", tags=["Fund — Agents"])


def get_factory(db: Session = Depends(get_db)) -> FundServiceFactory:
    return FundServiceFactory(session=db)


# ======================================================================
# Pools
# ======================================================================

@router.get("/agents", status_code=200)
def list_pools(
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Agentes abiertos al fondo con su capital, cola y participantes."""
    result = factory.agent_pools().list()
    return build_list_response(items=[pool_overview_to_dict(o) for o in result.data])


@router.get("/agents/eligible", status_code=200)
def list_eligible_agents(
    _identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Agentes sobre la billetera, con par en la moneda del fondo y sin pool."""
    result = factory.agent_pools().eligible()
    return build_list_response(items=[agent_info_to_dict(a) for a in result.data])


@router.post("/agents", status_code=201)
def open_pool(
    payload: OpenPoolRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Abre un agente al fondo: desde ahora puede recibir dinero de los participantes."""
    result = factory.agent_pools().open(payload.bot_id, int(identity["user_id"]))
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    detail = factory.agent_pools().detail(result.data.id).data
    return build_created_response(
        data=pool_detail_to_dict(detail),
        msg="Agente abierto al fondo. Asígnale dinero y liquídalo para que empiece a operarlo.",
    )


@router.get("/agents/{pool_id}", status_code=200)
def get_pool(
    pool_id: int,
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Detalle de un agente del fondo: participantes, cola y liquidaciones."""
    result = factory.agent_pools().detail(pool_id)
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=pool_detail_to_dict(result.data))


# ======================================================================
# Asignaciones
# ======================================================================

@router.post("/agents/{pool_id}/allocations", status_code=201)
def queue_allocation(
    pool_id: int,
    payload: QueueAllocationRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Pone en cola dinero de una persona para este agente (entra al liquidar)."""
    result = factory.allocations().queue(
        pool_id=pool_id,
        user_id=payload.user_id,
        amount=payload.amount,
        source_bucket=payload.source_bucket,
        requester_user_id=int(identity["user_id"]),
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=allocation_to_dict(result.data),
        msg="Asignación en cola. Entra al agente en la próxima liquidación.",
    )


@router.post("/allocations/{order_id}/cancel", status_code=200)
def cancel_allocation(
    order_id: int,
    _identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Saca una asignación de la cola (el dinero sigue en el saldo de la persona)."""
    result = factory.allocations().cancel(order_id)
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=allocation_to_dict(result.data), msg="Asignación cancelada.")


# ======================================================================
# Liquidación
# ======================================================================

@router.get("/agents/{pool_id}/settlement-preview", status_code=200)
def preview_settlement(
    pool_id: int,
    _identity: dict = Depends(staff_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """La liquidación calculada con los datos de ahora, sin escribir nada."""
    result = factory.settle_agent().preview(pool_id)
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    data = settlement_preview_to_dict(result.data)
    # Motivos que impiden liquidar, ya en texto de UI
    data["blocker_messages"] = [FUND_ERROR_MESSAGES.get(c, c) for c in result.data.blockers]
    return build_success_response(data=data)


@router.post("/agents/{pool_id}/settle", status_code=201)
def settle_agent(
    pool_id: int,
    payload: SettleRequest,
    identity: dict = Depends(super_admin_required),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Liquida el agente: equity exacta, NAV y aplica las asignaciones en cola."""
    result = factory.settle_agent().settle(
        pool_id, requester_user_id=int(identity["user_id"]), note=payload.note
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=settlement_to_dict(result.data),
        msg="Liquidación hecha. Ya puedes reanudar el agente.",
    )


# ======================================================================
# Participante
# ======================================================================

@router.get("/me/participations", status_code=200)
def my_participations(
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """En qué agentes está mi dinero y cuánto vale a la última liquidación."""
    result = factory.participations().mine(int(identity["user_id"]))
    return build_list_response(items=[participation_to_dict(p) for p in result.data])


# ======================================================================
# Salidas de los agentes (F5)
# ======================================================================

@router.post("/redemptions", status_code=201)
def request_redemption(
    payload: RedemptionCreateRequest,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """
    Pide sacar dinero de un agente: se aplica en su próxima liquidación.
    Un super admin puede pedirla por otra persona (`user_id`).
    """
    requester = int(identity["user_id"])
    user_id = payload.user_id if payload.user_id and is_super_admin(identity) else requester
    result = factory.redemptions().request(
        pool_id=payload.pool_id,
        user_id=user_id,
        amount=payload.amount,
        requester_user_id=requester,
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_created_response(
        data=redemption_request_to_dict(result.data),
        msg="Salida en cola. Se aplica en la próxima liquidación del agente.",
    )


@router.post("/redemptions/{request_id}/cancel", status_code=200)
def cancel_redemption(
    request_id: int,
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Anula una salida en cola (la propia; un super admin, cualquiera)."""
    result = factory.redemptions().cancel(
        request_id,
        requester_user_id=int(identity["user_id"]),
        is_manager=is_super_admin(identity),
    )
    if not result.success:
        return build_error_response(result, FUND_ERROR_MESSAGES)
    return build_success_response(data=redemption_request_to_dict(result.data), msg="Salida anulada.")


@router.get("/me/redemptions", status_code=200)
def my_redemptions(
    identity: dict = Depends(token_required_actual),
    factory: FundServiceFactory = Depends(get_factory),
):
    """Mis salidas: en cola, historial y lo que salió con su comisión tramo por tramo."""
    data = factory.redemptions().mine(int(identity["user_id"])).data
    return build_success_response(
        data={
            "queued":  [redemption_request_to_dict(r) for r in data.queued],
            "history": [redemption_request_to_dict(r) for r in data.history],
            "lines":   [settlement_redemption_to_dict(line) for line in data.lines],
        }
    )

