# app/modules/users/domain/user_repository.py
# -*- coding: utf-8 -*-

# ======================================================================
# User Repository Contract (Domain Port)
# ----------------------------------------------------------------------
# Patrón aplicado: Repository Pattern (Puerto / Contrato de Dominio)
#
# CAMBIOS:
# - No cambia la interfaz, pero la entidad User ahora incluye
#   login_locked_until y role_id.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.users.domain.user_entity import User


class UserRepository(ABC):
    """
    Contrato (interface) para persistencia/consulta de usuarios.
    """

    # ------------------------------------------------------------------
    # Lecturas
    # ------------------------------------------------------------------

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retorna un User si existe, o None si no existe."""
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Retorna un User si existe, o None si no existe."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Escrituras
    # ------------------------------------------------------------------

    @abstractmethod
    def create(self, user: User) -> User:
        """Crea un usuario y retorna el persistido."""
        raise NotImplementedError

    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un usuario y retorna el actualizado."""
        raise NotImplementedError