# app/modules/users/infrastructure/user_repository_impl.py
# -*- coding: utf-8 -*-

# ======================================================================
# SQLAlchemy User Repository Implementation (Infrastructure Adapter)
# ----------------------------------------------------------------------
# Patrón aplicado: Repository Pattern (Adaptador)
# - Implementa el contrato UserRepository (definido en domain/)
# - Usa SQLAlchemy + Session para hablar con la DB.
# - Traduce entre:
#     UserModel (ORM / infraestructura)  <->  User (entidad / dominio)
# ======================================================================

from __future__ import annotations

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
    - NO contiene reglas de negocio (eso va en services/domain)
    """

    def __init__(self, session: Session):
        # --------------------------------------------------------------
        # Inyección de dependencia: Session SQLAlchemy
        # (El commit/rollback idealmente lo decide el service o una UoW)
        # --------------------------------------------------------------
        self._session = session

    # ==================================================================
    # Mappers (Infra <-> Dominio)
    # ------------------------------------------------------------------
    # Nota arquitectónica:
    # - Este mapeo ES responsabilidad de infraestructura.
    # - Evita que el dominio conozca SQLAlchemy.
    # ==================================================================

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        """Convierte un modelo ORM (UserModel) a entidad de dominio (User)."""
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            password_hash=model.password_hash,
            role=model.role,
            status=model.status,
            failed_attempts=model.failed_attempts,
            last_login_at=model.last_login_at,
            token_current_jti=model.token_current_jti,
            otp_code=model.otp_code,
            otp_created_at=model.otp_created_at,
            otp_expires_at=model.otp_expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _apply_domain_to_model(user: User, model: UserModel) -> UserModel:
        """
        Copia los campos del User (dominio) al UserModel (ORM).

        Decisión:
        - created_at/updated_at NO se setean manualmente; los controla la DB.
        """
        model.email = user.email
        model.full_name = user.full_name
        model.password_hash = user.password_hash
        model.role = user.role
        model.status = user.status
        model.failed_attempts = user.failed_attempts
        model.last_login_at = user.last_login_at
        model.token_current_jti = user.token_current_jti
        model.otp_code = user.otp_code
        model.otp_created_at = user.otp_created_at
        model.otp_expires_at = user.otp_expires_at
        return model

    # ==================================================================
    # Implementación del contrato (UserRepository)
    # ==================================================================

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por PK.

        Retorna:
        - User (dominio) si existe
        - None si no existe
        """
        model: Optional[UserModel] = self._session.get(UserModel, user_id)
        return None if model is None else self._to_domain(model)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email (UNIQUE).

        Retorna:
        - User (dominio) si existe
        - None si no existe
        """
        model: Optional[UserModel] = (
            self._session.query(UserModel)
            .filter(UserModel.email == email)
            .one_or_none()
        )
        return None if model is None else self._to_domain(model)

    def create(self, user: User) -> User:
        """
        Crea un usuario.

        Nota:
        - Se hace flush para obtener el id generado sin necesidad de commit.
        - Se hace refresh para traer defaults/timestamps.
        """
        model = UserModel()

        # --------------------------------------------------------------
        # 1) Aplicar datos de dominio al ORM
        # --------------------------------------------------------------
        self._apply_domain_to_model(user, model)

        # --------------------------------------------------------------
        # 2) Persistir (sin decidir commit)
        # --------------------------------------------------------------
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)

        return self._to_domain(model)

    def update(self, user: User) -> User:
        """
        Actualiza un usuario existente.

        Estrategia:
        1) Cargar por id
        2) Mutar campos
        3) flush + refresh
        """
        model: Optional[UserModel] = self._session.get(UserModel, user.id)
        if model is None:
            # Infra no retorna ServiceResult (eso es del service).
            # Lanzamos un error para que el service lo convierta a fail().
            raise ValueError(f"User not found for update: id={user.id}")

        self._apply_domain_to_model(user, model)

        self._session.flush()
        self._session.refresh(model)

        return self._to_domain(model)