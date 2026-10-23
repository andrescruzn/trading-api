# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/telegram/routes.py
#
# ENDPOINTS:
# - POST   /users/me/telegram/link → enlace de un solo uso para vincular el chat
# - DELETE /users/me/telegram      → desvincular el chat
#
# El estado (vinculado o no) viaja en GET /users/me → telegram_linked.
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_success_response
from app.common.security.jwt import token_required_actual
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.users.providers import AuthServiceFactory, get_auth_factory

from .error_messages import TELEGRAM_LINK_ERROR_MESSAGES

router = APIRouter(prefix="/users/me/telegram", tags=["Telegram"])


def get_factory(db: Session = Depends(get_db)) -> AuthServiceFactory:
    return get_auth_factory(db)


# ======================================================================
# POST /users/me/telegram/link
# ======================================================================

@router.post("/link", status_code=200)
def create_telegram_link(
    identity: dict = Depends(token_required_actual),
    factory: AuthServiceFactory = Depends(get_factory),
):
    result = factory.telegram_link().create_link(user_id=int(identity["user_id"]))
    if not result.success:
        return build_error_response(result, TELEGRAM_LINK_ERROR_MESSAGES)

    return build_success_response(
        data={
            "link_url": result.data.link_url,
            "expires_at": to_iso_utc(result.data.expires_at),
        },
        msg="Abre el enlace en Telegram y pulsa Iniciar para vincular tu chat.",
    )


# ======================================================================
# DELETE /users/me/telegram
# ======================================================================

@router.delete("", status_code=200)
def unlink_telegram(
    identity: dict = Depends(token_required_actual),
    factory: AuthServiceFactory = Depends(get_factory),
):
    result = factory.telegram_link().unlink(user_id=int(identity["user_id"]))
    if not result.success:
        return build_error_response(result, TELEGRAM_LINK_ERROR_MESSAGES)

    return build_success_response(data={"telegram_linked": False}, msg="Telegram desvinculado.")
