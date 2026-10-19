# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/telegram/telegram_link_service.py
#
# PROPÓSITO:
# - Vincular el chat privado de Telegram de un usuario para recibir las
#   señales por aprobar (con botones Aprobar / Rechazar).
#
# FLUJO:
#   1. create_link(user_id): genera un código de un solo uso (10 min) y
#      devuelve el enlace https://t.me/<bot>?start=<código>.
#   2. La persona abre el enlace y pulsa Iniciar; Telegram envía
#      "/start <código>" al bot.
#   3. confirm(code, chat_id): busca el código (guardado como SHA-256),
#      guarda el chat y borra el código.
#
# SEGURIDAD:
# - En BD solo queda el hash del código; el código viaja una vez.
# - Un chat solo pertenece a un usuario (UNIQUE): si ya estaba vinculado a
#   otro, se le quita a ese otro.
# ======================================================================

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.common.config.settings import Settings
from app.common.contracts import ServiceResult
from app.common.utils import ensure_aware_utc, utc_now
from app.modules.users.domain import UserRepository
from app.modules.users.domain.user_entity import User

_LINK_TTL_MINUTES = 10


@dataclass(frozen=True)
class TelegramLink:
    link_url: str
    expires_at: datetime


def hash_link_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class TelegramLinkService:
    """Vincula, confirma y desvincula el chat de Telegram de un usuario."""

    def __init__(self, *, repo: UserRepository, settings: Settings):
        self._repo = repo
        self._settings = settings

    def create_link(self, user_id: int) -> ServiceResult[TelegramLink]:
        if not self._settings.TELEGRAM_BOT_TOKEN or not self._settings.TELEGRAM_BOT_USERNAME:
            return ServiceResult.fail(code="TELEGRAM_NOT_CONFIGURED", http_status=503)

        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        # token_urlsafe solo usa [A-Za-z0-9_-]: válido como parámetro de /start
        code = secrets.token_urlsafe(24)
        expires_at = utc_now() + timedelta(minutes=_LINK_TTL_MINUTES)
        user.telegram_link_hash = hash_link_code(code)
        user.telegram_link_expires_at = expires_at
        self._repo.update(user)
        self._repo.commit()

        return ServiceResult.ok(
            TelegramLink(
                link_url=f"https://t.me/{self._settings.TELEGRAM_BOT_USERNAME}?start={code}",
                expires_at=expires_at,
            )
        )

    def confirm(self, code: str, chat_id: int) -> ServiceResult[User]:
        if not code or len(code) > 64:
            return ServiceResult.fail(code="TELEGRAM_LINK_INVALID", http_status=400)

        user = self._repo.get_by_telegram_link_hash(hash_link_code(code))
        if user is None:
            return ServiceResult.fail(code="TELEGRAM_LINK_INVALID", http_status=400)

        expires_at = ensure_aware_utc(user.telegram_link_expires_at)
        if expires_at is None or expires_at < utc_now():
            return ServiceResult.fail(code="TELEGRAM_LINK_INVALID", http_status=400)

        previous = self._repo.get_by_telegram_chat_id(int(chat_id))
        if previous is not None and previous.id != user.id:
            previous.telegram_chat_id = None
            self._repo.update(previous)

        user.telegram_chat_id = int(chat_id)
        user.telegram_link_hash = None
        user.telegram_link_expires_at = None
        updated = self._repo.update(user)
        self._repo.commit()
        return ServiceResult.ok(updated)

    def unlink(self, user_id: int) -> ServiceResult[None]:
        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        user.telegram_chat_id = None
        user.telegram_link_hash = None
        user.telegram_link_expires_at = None
        self._repo.update(user)
        self._repo.commit()
        return ServiceResult.ok(None)
