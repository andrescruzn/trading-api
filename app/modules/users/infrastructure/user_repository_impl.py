# app/modules/users/infrastructure/user_repository_impl.py
# -*- coding: utf-8 -*-

# ======================================================================
# SQLAlchemy User Repository Implementation (Infrastructure Adapter)
# ----------------------------------------------------------------------
# Patrón aplicado: Repository Pattern (Adaptador)
#
# FIX CRÍTICO (TIMEZONES):
# - MySQL/SQLAlchemy suele retornar TIMESTAMP/DATETIME como "naive"
#   (sin tzinfo).
# - Nuestro dominio/services trabajan con "UTC aware" (timezone.utc).
# - Normalizamos aquí para evitar errores de comparación y mantener
#   consistencia en todo el sistema.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.users.domain.user_entity import User
from app.modules.users.domain.user_repository import UserRepository
from app.modules.users.infrastructure.user_model import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """
    Repositorio concreto usando SQLAlchemy.

    Responsabilidad (SRP):
    - Ejecutar queries (infra)
    - Mapear ORM <-> Dominio
    - Normalizar tipos infra (ej: datetimes) a lo esperado por el dominio
    """

    def __init__(self, session: Session):
        self._session = session

    # ==================================================================
    # Helpers (Infra): Normalización de datetimes
    # ==================================================================

    @staticmethod
    def _as_utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
        """
        Convierte datetime potencialmente naive -> UTC aware.

        Decisión:
        - Si dt viene sin tzinfo (naive), asumimos que representa UTC.
          (Esto es correcto SI tu conexión/DB opera en UTC; abajo te dejo
          el ajuste recomendado en engine).
        """
        if dt is None:
            return None

        # Si viene naive (lo típico con MySQL), lo marcamos como UTC.
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)

        # Si viene aware, lo convertimos a UTC por consistencia.
        return dt.astimezone(timezone.utc)

    # ==================================================================
    # Mappers (Infra <-> Dominio)
    # ==================================================================

    def _to_domain(self, model: UserModel) -> User:
        """
        Convierte ORM -> Dominio (normalizando timestamps).
        """
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            password_hash=model.password_hash,
            role_id=model.role_id,
            status=model.status,
            failed_attempts=model.failed_attempts,
            login_locked_until=self._as_utc_aware(model.login_locked_until),
            last_login_at=self._as_utc_aware(model.last_login_at),
            token_current_jti=model.token_current_jti,
            otp_code=model.otp_code,
            otp_created_at=self._as_utc_aware(model.otp_created_at),
            otp_expires_at=self._as_utc_aware(model.otp_expires_at),
            created_at=self._as_utc_aware(model.created_at),
            updated_at=self._as_utc_aware(model.updated_at),
        )

    @staticmethod
    def _apply_domain_to_model(user: User, model: UserModel) -> UserModel:
        """
        Copia Dominio -> ORM.

        Decisión:
        - created_at/updated_at NO se setean manualmente (DB manda).
        - Guardamos datetimes tal cual vengan del dominio.
          (Como el dominio ya opera en UTC aware, esto queda consistente)
        """
        model.email = user.email
        model.full_name = user.full_name
        model.password_hash = user.password_hash

        model.role_id = user.role_id

        model.status = user.status
        model.failed_attempts = user.failed_attempts
        model.login_locked_until = user.login_locked_until
        model.last_login_at = user.last_login_at

        model.token_current_jti = user.token_current_jti

        model.otp_code = user.otp_code
        model.otp_created_at = user.otp_created_at
        model.otp_expires_at = user.otp_expires_at

        return model

    # ==================================================================
    # Contract
    # ==================================================================

    def get_by_id(self, user_id: int) -> Optional[User]:
        model: Optional[UserModel] = self._session.get(UserModel, user_id)
        return None if model is None else self._to_domain(model)

    def get_by_email(self, email: str) -> Optional[User]:
        model: Optional[UserModel] = (
            self._session.query(UserModel)
            .filter(UserModel.email == email)
            .one_or_none()
        )
        return None if model is None else self._to_domain(model)

    def create(self, user: User) -> User:
        model = UserModel()
        self._apply_domain_to_model(user, model)

        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)

        return self._to_domain(model)

    def update(self, user: User) -> User:
        model: Optional[UserModel] = self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User not found for update: id={user.id}")

        self._apply_domain_to_model(user, model)

        self._session.flush()
        self._session.refresh(model)

        return self._to_domain(model)