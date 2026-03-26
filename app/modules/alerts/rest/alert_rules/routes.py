# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/rest/alert_rules/routes.py
#
# ENDPOINTS:
# - GET    /api/alert-rules           → listar reglas (user ve las suyas, admin ve todas)
# - POST   /api/alert-rules           → crear nueva regla
# - GET    /api/alert-rules/{id}      → detalle de regla
# - PUT    /api/alert-rules/{id}      → actualizar regla
# - DELETE /api/alert-rules/{id}      → desactivar regla (soft delete)
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    send,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.alerts.domain.alert_rule_entity import AlertRule
from app.modules.alerts.providers import AlertServiceFactory, get_alert_factory

from .error_messages import ALERT_RULE_ERROR_MESSAGES
from .schemas import CreateAlertRuleRequest, UpdateAlertRuleRequest

router = APIRouter(prefix="/api/alert-rules", tags=["Alert Rules"])


def get_factory(db: Session = Depends(get_db)) -> AlertServiceFactory:
    return get_alert_factory(db)


def _rule_to_dict(r: AlertRule) -> dict[str, Any]:
    return {
        "id":         r.id,
        "name":       r.name,
        "rule_type":  r.rule_type,
        "rule_spec":  r.rule_spec,
        "channels":   r.channels,
        "is_active":  r.is_active,
        "user_id":    r.user_id,
        "bot_id":     r.bot_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ======================================================================
# GET /api/alert-rules
# ======================================================================

@router.get("", status_code=200)
def list_alert_rules(
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    user_id = identity.get("user_id")

    result = factory.list_alert_rules().list(user_id=user_id, is_admin=is_admin)
    return build_list_response(
        items=[_rule_to_dict(r) for r in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /api/alert-rules
# ======================================================================

@router.post("", status_code=201)
def create_alert_rule(
    payload: CreateAlertRuleRequest,
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    user_id = identity.get("user_id")

    result = factory.create_alert_rule().create(
        name=payload.name,
        rule_type=payload.rule_type,
        rule_spec=payload.rule_spec,
        channels=payload.channels,
        user_id=user_id,
        bot_id=payload.bot_id,
    )

    if not result.success:
        return build_error_response(result, ALERT_RULE_ERROR_MESSAGES)

    return build_created_response(data=_rule_to_dict(result.data), msg="Regla creada.")


# ======================================================================
# GET /api/alert-rules/{id}
# ======================================================================

@router.get("/{rule_id}", status_code=200)
def get_alert_rule(
    rule_id: int,
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    from app.modules.alerts.infrastructure import SqlAlchemyAlertRuleRepository
    from app.extensions.db import get_db as _get_db

    # Direct repo lookup since we don't have a dedicated GetService
    repo = factory._rule_repo
    rule = repo.get_by_id(rule_id)
    if rule is None:
        return send(msg="Regla de alerta no encontrada.", status_code=404, data={})

    # Ownership check (non-admin can only see their own)
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    if not is_admin and rule.user_id != identity.get("user_id"):
        return send(msg="Regla de alerta no encontrada.", status_code=404, data={})

    return send(msg="OK", status_code=200, data=_rule_to_dict(rule))


# ======================================================================
# PUT /api/alert-rules/{id}
# ======================================================================

@router.put("/{rule_id}", status_code=200)
def update_alert_rule(
    rule_id: int,
    payload: UpdateAlertRuleRequest,
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    # Ownership check before update
    repo = factory._rule_repo
    rule = repo.get_by_id(rule_id)
    if rule is None:
        return send(msg="Regla de alerta no encontrada.", status_code=404, data={})

    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    if not is_admin and rule.user_id != identity.get("user_id"):
        return send(msg="Regla de alerta no encontrada.", status_code=404, data={})

    result = factory.update_alert_rule().update(
        rule_id=rule_id,
        name=payload.name,
        rule_spec=payload.rule_spec,
        channels=payload.channels,
        is_active=payload.is_active,
    )

    if not result.success:
        return build_error_response(result, ALERT_RULE_ERROR_MESSAGES)

    return send(msg="Regla actualizada.", status_code=200, data=_rule_to_dict(result.data))


# ======================================================================
# DELETE /api/alert-rules/{id}  → soft delete (is_active = False)
# ======================================================================

@router.delete("/{rule_id}", status_code=200)
def delete_alert_rule(
    rule_id: int,
    identity: dict = Depends(token_required_actual),
    factory: AlertServiceFactory = Depends(get_factory),
):
    repo = factory._rule_repo
    rule = repo.get_by_id(rule_id)
    if rule is None:
        return send(msg="Regla de alerta no encontrada.", status_code=404, data={})

    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)
    if not is_admin and rule.user_id != identity.get("user_id"):
        return send(msg="Regla de alerta no encontrada.", status_code=404, data={})

    result = factory.update_alert_rule().update(rule_id=rule_id, is_active=False)
    if not result.success:
        return build_error_response(result, ALERT_RULE_ERROR_MESSAGES)

    return send(msg="Regla desactivada.", status_code=200, data={})
