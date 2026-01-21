# app/modules/users/domain/__init__.py
# Barrel exports del paquete users.domain
from .user_entity import User
from .user_repository import UserRepository

__all__ = ["User", "UserRepository"]