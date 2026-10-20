# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/infrastructure/__init__.py
#
# PROPÓSITO:
# - Barrel exports del layer infrastructure del módulo users.
#
# CLAVE:
# - Importar modelos ORM aquí asegura que SQLAlchemy registre
#   las tablas en Base.metadata (incluyendo roles).
# ======================================================================

from .user_model import UserModel
from .role_model import RoleModel

from .user_repository_impl import SqlAlchemyUserRepository

# SqlAlchemyAuditEventRepository no se exporta aquí: importa app.common.audit,
# que vuelve a jwt_guard → este paquete (ciclo). Importarlo por su ruta.

__all__ = [
    "UserModel",
    "RoleModel",
    "SqlAlchemyUserRepository",
]