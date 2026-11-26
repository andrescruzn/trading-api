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

from sqlalchemy import BigInteger, CheckConstraint, Column, String, UniqueConstraint, text
from sqlalchemy.dialects.mysql import TIMESTAMP, TINYINT

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class RoleModel(Base):
    """
    Modelo ORM para la tabla `roles`.
    """

    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("code", name="uq_roles_code"),
        CheckConstraint("`code` <> ''", name="chk_roles_code"),
        MYSQL_TABLE_OPTIONS,
    )

    # --------------------------------------------------------------
    # PK
    # --------------------------------------------------------------
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # --------------------------------------------------------------
    # Campos de negocio mínimos (según tu DDL)
    # --------------------------------------------------------------
    code = Column(String(32), nullable=False)
    name = Column(String(120), nullable=False)

    # tinyint(1) en MySQL; se expone como int (no Boolean) para no cambiar
    # el tipo Python que ya consume el código.
    is_active = Column(
        TINYINT(1),
        nullable=False,
        server_default=text("'1'"),
    )

    # --------------------------------------------------------------
    # Auditoría
    # --------------------------------------------------------------
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
