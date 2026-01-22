# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/infrastructure/role_model.py
#
# PROPÓSITO:
# - Registrar en el metadata de SQLAlchemy la tabla `roles`
#
# POR QUÉ ES NECESARIO:
# - Aunque la tabla ya exista en MySQL, SQLAlchemy necesita conocerla
#   en su "Base.metadata" para resolver Foreign Keys al hacer flush().
#
# IMPORTANTE:
# - Este modelo NO es dominio. Es solo infraestructura (ORM).
# - No estás obligado a crear un repositorio de roles todavía.
# ======================================================================

from sqlalchemy import BigInteger, Column, String, TIMESTAMP, text
from app.extensions.db import Base


class RoleModel(Base):
    """
    Modelo ORM para la tabla `roles`.
    """

    __tablename__ = "roles"

    # --------------------------------------------------------------
    # PK
    # --------------------------------------------------------------
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # --------------------------------------------------------------
    # Campos de negocio mínimos (según tu DDL)
    # --------------------------------------------------------------
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(120), nullable=False)

    # tinyint(1) en MySQL -> lo dejamos como int simple para no complicar
    # (puedes cambiarlo a Boolean si quieres)
    is_active = Column(
        BigInteger,  # si prefieres, cámbialo a Integer
        nullable=False,
        server_default=text("1"),
    )

    # --------------------------------------------------------------
    # Auditoría
    # --------------------------------------------------------------
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )