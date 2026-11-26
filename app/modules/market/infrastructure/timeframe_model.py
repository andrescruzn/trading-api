# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/timeframe_model.py
#
# Modelo SQLAlchemy para la tabla `timeframes`.
# ======================================================================

from sqlalchemy import CheckConstraint, Column, Integer, SmallInteger, String, UniqueConstraint

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class TimeframeModel(Base):
    """Modelo SQLAlchemy para la tabla `timeframes`."""

    __tablename__ = "timeframes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_timeframes_code"),
        CheckConstraint("`seconds` > 0", name="chk_timeframes_seconds"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(8), nullable=False)
    seconds = Column(Integer, nullable=False)
