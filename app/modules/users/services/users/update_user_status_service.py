# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/users/update_user_status_service.py
#
# CASO DE USO:
# - Un admin cambia el estado de la cuenta de otro usuario:
#   active (puede entrar) · blocked (suspensión temporal, p. ej. actividad
#   sospechosa) · disabled (la cuenta ya no se usa). Blocked y disabled
#   impiden entrar por igual; la diferencia es solo de significado.
#
# REGLAS:
# - Nadie cambia su propio estado (como con el rol): un admin no se deja
#   fuera por error y el sistema nunca se queda sin admin activo.
# - Si el estado no cambia, no se escribe nada.
# - Al pasar a blocked/disabled se revoca la sesión (token_current_jti =
#   None) y se borra el código de entrada pendiente: el efecto es inmediato
#   aunque el guard JWT ya rechace a quien no está activo.
# - Al pasar a blocked/disabled se PAUSAN sus agentes `running` en el mismo
#   commit: sin señales ni órdenes nuevas mientras nadie puede supervisarlos.
#   `paused` (no `stopped`) para que el scheduler siga bajando velas y el
#   SL/TP de las posiciones abiertas siga vigilado. Al reactivar la cuenta
#   no se reanudan solos: la persona decide.
# ======================================================================

from __future__ import annotations

from typing import TYPE_CHECKING

from app.common.contracts import ServiceResult
from app.modules.users.domain import UserRepository
from app.modules.users.services.users.list_users_service import UserSummaryPayload

if TYPE_CHECKING:
    from app.modules.accounts.domain.account_repository import AccountRepository
    from app.modules.bots.domain.bot_repository import BotRepository

# Valores permitidos por el CHECK `chk_users_status` de la tabla `users`.
USER_STATUSES: tuple[str, ...] = ("active", "blocked", "disabled")


class UpdateUserStatusService:
    """Activa, bloquea o desactiva la cuenta de un usuario (solo admin)."""

    def __init__(
        self,
        *,
        repo: UserRepository,
        bot_repo: "BotRepository | None" = None,
        account_repo: "AccountRepository | None" = None,
    ):
        self._repo = repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def update(
        self,
        user_id: int,
        status: str,
        requester_user_id: int,
    ) -> ServiceResult[UserSummaryPayload]:
        new_status = (status or "").strip().lower()
        if new_status not in USER_STATUSES:
            return ServiceResult.fail(code="USER_INVALID_STATUS", http_status=422)

        if int(user_id) == int(requester_user_id):
            return ServiceResult.fail(code="USER_CANNOT_CHANGE_OWN_STATUS", http_status=422)

        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        if user.status != new_status:
            user.status = new_status
            if new_status != "active":
                # Cierra la sesión abierta y anula el código que tuviera pedido.
                user.token_current_jti = None
                user.otp_code = None
                user.otp_created_at = None
                user.otp_expires_at = None
                user.otp_failed_attempts = 0
            try:
                user = self._repo.update(user)
                if new_status != "active":
                    self._pause_running_bots(user.id)
                self._repo.commit()
            except Exception:
                self._repo.rollback()
                raise

        role = self._repo.get_role_info(int(user.role_id)) or {"code": "", "name": ""}
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

    def _pause_running_bots(self, user_id: int) -> int:
        """Pausa los agentes `running` de las cuentas del usuario (sin commit)."""
        if self._bot_repo is None or self._account_repo is None:
            return 0
        account_ids = [a.id for a in self._account_repo.list_by_user_id(user_id)]
        if not account_ids:
            return 0
        paused = 0
        for bot in self._bot_repo.list_by_account_ids(account_ids):
            if bot.status == "running" and bot.can_transition_to("paused"):
                bot.status = "paused"
                self._bot_repo.update(bot)
                paused += 1
        return paused
