# app/modules/users/domain/user_repository.py
# -*- coding: utf-8 -*-

# ======================================================================
# User Repository Contract (Domain Port)
# ----------------------------------------------------------------------
# Patrón aplicado: Repository Pattern (Puerto / Contrato de Dominio)
# - Define las operaciones que el dominio necesita para acceder/persistir
#   usuarios sin acoplarse a SQLAlchemy ni a la DB.
# - La infraestructura implementará este contrato (adaptador).
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.users.domain.user_entity import User


class UserRepository(ABC):
    """
    Contrato (interface) para persistencia/consulta de usuarios.

    Responsabilidad:
    - Definir "qué" operaciones se necesitan.
    - No definir "cómo" (eso lo hace infrastructure/).
    """

    # ------------------------------------------------------------------
    # Lecturas
    # ------------------------------------------------------------------

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retorna un User si existe, o None si no existe.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retorna un User si existe, o None si no existe.
        Nota:
        - Email es UNIQUE según el esquema.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Escrituras
    # ------------------------------------------------------------------

    @abstractmethod
    def create(self, user: User) -> User:
        """
        Crea un usuario.

        Retorna:
        - El User persistido (normalmente ya con id y timestamps poblados).
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, user: User) -> User:
        """
        Actualiza un usuario existente y retorna el User actualizado.
        """
        raise NotImplementedError