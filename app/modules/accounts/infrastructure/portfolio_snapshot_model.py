# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/portfolio_snapshot_model.py
#
# Modelo SQLAlchemy para la tabla `portfolio_snapshots`.
#
# NOTAS:
# - Foto periódica del portafolio de un bot: equity, cash y PnL realizado /
#   no realizado (base para curvas de equity y drawdown).
# - Hoy ningún servicio escribe en esta tabla; el modelo existe para que el
#   esquema completo lo gestione Alembic.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, DECIMAL, ForeignKey, Index, JSON, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class PortfolioSnapshotModel(Base):
    """Modelo SQLAlchemy para la tabla `portfolio_snapshots`."""

    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        Index("idx_snapshots_bot_ts", "bot_id", "ts"),
        CheckConstraint("json_valid(`meta`)", name="chk_snapshots_meta_json"),
        CheckConstraint("`equity` >= 0 AND `cash` >= 0", name="chk_snapshots_money"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(BigInteger, ForeignKey("bots.id", name="fk_snapshots_bot"), nullable=False)
    ts = Column(TIMESTAMP(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    equity = Column(DECIMAL(30, 12), nullable=False)
    cash = Column(DECIMAL(30, 12), nullable=False)
    unrealized_pnl = Column(DECIMAL(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    realized_pnl = Column(DECIMAL(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    meta = Column(JSON, nullable=False)
