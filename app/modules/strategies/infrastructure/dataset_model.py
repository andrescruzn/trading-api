# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/infrastructure/dataset_model.py
#
# Modelo SQLAlchemy para la tabla `datasets`.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, JSON, SmallInteger, String, Text, TIMESTAMP, text

from app.extensions.db import Base


class DatasetModel(Base):
    """Modelo SQLAlchemy para la tabla `datasets`."""

    __tablename__ = "datasets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id"),
        nullable=True,
        index=True,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id"),
        nullable=True,
        index=True,
    )
    start_ts = Column(TIMESTAMP(6), nullable=True)
    end_ts = Column(TIMESTAMP(6), nullable=True)
    dataset_hash = Column(String(128), nullable=True)
    query_spec = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
