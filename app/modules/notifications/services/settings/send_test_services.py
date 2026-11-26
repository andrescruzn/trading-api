# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/notifications/services/settings/send_test_services.py
#
# CASOS DE USO (super admin): comprobar que cada canal entrega.
# - SendTelegramTestService.send(...) → al chat que vinculó quien prueba;
#   si no vinculó, al chat por defecto (TELEGRAM_NO_CHAT si no hay ninguno).
# - SendEmailTestService.send(...)    → al correo de quien prueba; se
#   envía en el momento (no en segundo plano) para informar el resultado.
#   Funciona con el canal apagado: sirve para probar antes de encenderlo.
#
# Los textos los pasa la ruta (los servicios no definen textos de UI).
# ======================================================================

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.common.contracts import ServiceResult
from app.modules.mailer.domain.mail_template import NOTICE_TEMPLATE
from app.modules.notifications.domain import NotificationSettingsReader, TelegramGateway
from app.modules.users.domain import UserRepository

if TYPE_CHECKING:
    from app.modules.mailer.services.mailer_service import MailerService


class SendTelegramTestService:

    def __init__(
        self,
        *,
        reader: NotificationSettingsReader,
        user_repo: UserRepository,
        gateway: TelegramGateway,
    ):
        self._reader = reader
        self._user_repo = user_repo
        self._gateway = gateway

    def send(self, *, requester_user_id: int, text: str) -> ServiceResult[dict[str, Any]]:
        settings = self._reader.get()
        if not settings.telegram_active:
            return ServiceResult.fail(code="TELEGRAM_NOT_ACTIVE", http_status=409)

        user = self._user_repo.get_by_id(int(requester_user_id))
        own_chat = user.telegram_chat_id if user else None
        chat_id = own_chat or settings.telegram_default_chat_id
        if not chat_id:
            return ServiceResult.fail(code="TELEGRAM_NO_CHAT", http_status=422)

        if not self._gateway.send_message(settings.telegram_token, chat_id, text):
            return ServiceResult.fail(code="TELEGRAM_SEND_FAILED", http_status=502)
        return ServiceResult.ok({"target": "own_chat" if own_chat else "default_chat"})


class SendEmailTestService:

    def __init__(self, *, user_repo: UserRepository, mailer: "MailerService | None"):
        self._user_repo = user_repo
        self._mailer = mailer

    def send(
        self,
        *,
        requester_user_id: int,
        subject: str,
        title: str,
        message: str,
    ) -> ServiceResult[dict[str, Any]]:
        if self._mailer is None:
            return ServiceResult.fail(code="EMAIL_NOT_CONFIGURED", http_status=503)

        user = self._user_repo.get_by_id(int(requester_user_id))
        if user is None or not user.email:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        result = self._mailer.send_by_template(
            to_email=user.email,
            template=NOTICE_TEMPLATE,
            context={"title": title, "message": message, "full_name": user.full_name},
            subject_override=subject,
        )
        if not result.success:
            return ServiceResult.fail(code="EMAIL_SEND_FAILED", http_status=502)
        return ServiceResult.ok({"to_email": user.email})
