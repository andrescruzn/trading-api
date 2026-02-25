# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/exchange_model.py
#
# Modelo SQLAlchemy para la tabla `exchanges`.
# ======================================================================

from sqlalchemy import BigInteger, Boolean, Column, String, TIMESTAMP, text

from app.extensions.db import Base


class ExchangeModel(Base):
    """Modelo SQLAlchemy para la tabla `exchanges`."""

    __tablename__ = "exchanges"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True)
    type = Column(String(32), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
