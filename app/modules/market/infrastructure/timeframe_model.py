# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/timeframe_model.py
#
# Modelo SQLAlchemy para la tabla `timeframes`.
# ======================================================================

from sqlalchemy import Column, Integer, SmallInteger, String

from app.extensions.db import Base


class TimeframeModel(Base):
    """Modelo SQLAlchemy para la tabla `timeframes`."""

    __tablename__ = "timeframes"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(8), nullable=False, unique=True)
    seconds = Column(Integer, nullable=False)
