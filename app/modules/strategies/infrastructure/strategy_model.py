# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/infrastructure/strategy_model.py
#
# Modelo SQLAlchemy para la tabla `strategies`.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class StrategyModel(Base):
    """Modelo SQLAlchemy para la tabla `strategies`."""

    __tablename__ = "strategies"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_strategies_name_version"),
        CheckConstraint("json_valid(`parameters`)", name="chk_strategies_parameters_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    version = Column(String(32), nullable=False, server_default=text("'1.0.0'"))
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
