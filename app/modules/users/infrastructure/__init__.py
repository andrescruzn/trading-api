#. app/modules/users/infrastructure/__init__.py
# Barrel exports del paquete users.infrastructure
from .user_model import UserModel
from .user_repository_impl import SqlAlchemyUserRepository

__all__ = ["UserModel", "SqlAlchemyUserRepository"]