# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/infrastructure/strategy_model.py
#
# Modelo SQLAlchemy para la tabla `strategies`.
# ======================================================================

from sqlalchemy import BigInteger, Column, JSON, String, Text, TIMESTAMP, text

from app.extensions.db import Base


class StrategyModel(Base):
    """Modelo SQLAlchemy para la tabla `strategies`."""

    __tablename__ = "strategies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    version = Column(String(32), nullable=False, server_default=text("'1.0.0'"))
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
