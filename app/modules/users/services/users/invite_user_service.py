# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/users/invite_user_service.py
#
# CASO DE USO:
# - Un admin da de alta a una persona (registro solo por invitación):
#   correo, nombre y rol. Se le envía un correo de bienvenida y entra con
#   el código por correo de siempre (no hay contraseñas).
#
# REGLAS:
# - Correo válido y sin cuenta (USER_EMAIL_TAKEN si ya existe).
# - Rol por código (user / admin / investor) → ID con AUTH_*_ROLE_ID.
# - El correo sale en segundo plano: si falla, la cuenta ya existe y la
#   persona puede entrar igual pidiendo su código.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.common.utils import clean_email, clean_str
from app.modules.mailer.domain.mail_template import WELCOME_TEMPLATE
from app.modules.mailer.services.mailer_service import MailerService
from app.modules.users.domain import UserRepository
from app.modules.users.domain.user_entity import User
from app.modules.users.services.users.list_users_service import UserSummaryPayload


class InviteUserService:
    """Crea un usuario activo y le envía la bienvenida."""

    def __init__(
        self,
        *,
        repo: UserRepository,
        mailer: MailerService,
        role_ids: dict[str, int],
        login_url: str,
    ):
        self._repo = repo
        self._mailer = mailer
        self._role_ids = role_ids
        self._login_url = login_url

    def invite(
        self,
        email: str,
        role_code: str,
        full_name: str | None = None,
    ) -> ServiceResult[UserSummaryPayload]:
        try:
            email_clean = clean_email(email)
        except ValueError:
            return ServiceResult.fail(code="USER_INVALID_EMAIL", http_status=422)

        name = None
        if full_name and full_name.strip():
            try:
                name = clean_str(full_name, max_len=255)
            except ValueError:
                return ServiceResult.fail(code="USER_INVALID_NAME", http_status=422)

        role_id = self._role_ids.get(role_code)
        role = self._repo.get_role_info(role_id) if role_id is not None else None
        if role is None:
            return ServiceResult.fail(code="USER_INVALID_ROLE", http_status=422)

        if self._repo.get_by_email(email_clean) is not None:
            return ServiceResult.fail(code="USER_EMAIL_TAKEN", http_status=409)

        try:
            user = self._repo.create(
                User(id=0, email=email_clean, role_id=role_id, status="active", full_name=name)
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise

        self._mailer.send_by_template_in_background(
            to_email=email_clean,
            template=WELCOME_TEMPLATE,
            context={
                "full_name": name,
                "login_url": self._login_url,
                "email": email_clean,
                "title": "Te dieron acceso a Trading App",
            },
            text_body=(
                f"Te dieron acceso a Trading App. Entra en {self._login_url} con tu correo "
                f"({email_clean}): te enviaremos un código para iniciar sesión."
            ),
        )

        return ServiceResult.ok(
            UserSummaryPayload(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role_code=str(role["code"]),
                role_name=str(role["name"]),
                status=user.status,
                last_login_at=user.last_login_at,
            )
        )
