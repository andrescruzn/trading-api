# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/infrastructure/dataset_model.py
#
# Modelo SQLAlchemy para la tabla `datasets`.
#
# NOTA: el índice de `timeframe_id` lo crea MySQL solo, con el nombre de su
# FK (`fk_datasets_timeframe`): no se declara.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    JSON,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class DatasetModel(Base):
    """Modelo SQLAlchemy para la tabla `datasets`."""

    __tablename__ = "datasets"
    __table_args__ = (
        Index("idx_datasets_symbol_tf", "symbol_id", "timeframe_id"),
        CheckConstraint("json_valid(`query_spec`)", name="chk_datasets_query_spec_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id", name="fk_datasets_symbol"),
        nullable=True,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id", name="fk_datasets_timeframe"),
        nullable=True,
    )
    start_ts = Column(TIMESTAMP(fsp=6), nullable=True)
    end_ts = Column(TIMESTAMP(fsp=6), nullable=True)
    dataset_hash = Column(String(128), nullable=True)
    query_spec = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
