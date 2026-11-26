# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/infrastructure/agent_pool_models.py
#
# Modelos ORM del capital de los agentes en el fondo común (F4):
# - `agent_pools`: equity liquidada y unidades de cada agente.
# - `agent_settlements`: cada liquidación (equity exacta, NAV, entradas).
# - `unit_lots`: unidades de cada persona en cada agente.
# - `allocation_orders`: asignaciones en cola hasta la próxima liquidación.
# ======================================================================

from __future__ import annotations

from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import MYSQL_TABLE_OPTIONS, Base


class AgentPoolModel(Base):
    """El dinero de un agente en el fondo: equity liquidada y unidades."""

    __tablename__ = "agent_pools"
    __table_args__ = (
        UniqueConstraint("bot_id", name="uq_agent_pools_bot"),
        CheckConstraint("`equity` >= 0 AND `units` >= 0", name="chk_agent_pools_amounts"),
        CheckConstraint("`last_fill_id` >= 0", name="chk_agent_pools_last_fill"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_agent_pools_bot"),
        nullable=False,
        comment="Agente que opera este dinero",
    )
    asset = Column(String(16), nullable=False, comment="Moneda del pool (la del fondo, USDT)")
    equity = Column(
        DECIMAL(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
        comment="Equity exacta de la última liquidación",
    )
    units = Column(
        DECIMAL(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
        comment="Unidades en circulación; NAV = equity / units",
    )
    last_fill_id = Column(
        BigInteger,
        nullable=False,
        server_default=text("'0'"),
        comment="Último fill del bot ya contabilizado (lo anterior no cuenta)",
    )
    last_settlement_id = Column(BigInteger, nullable=True)
    last_funding_id = Column(
        BigInteger,
        nullable=False,
        server_default=text("'0'"),
        comment="Último funding (perpetuos) ya contabilizado",
    )
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_agent_pools_created_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )


class AgentSettlementModel(Base):
    """Liquidación de un agente: equity exacta, NAV y entradas aplicadas."""

    __tablename__ = "agent_settlements"
    __table_args__ = (
        Index("idx_agent_settlements_pool_settled", "pool_id", "settled_at"),
        CheckConstraint("json_valid(`unvalued_fees`)", name="chk_agent_settlements_fees_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pool_id = Column(
        BigInteger,
        ForeignKey("agent_pools.id", name="fk_agent_settlements_pool"),
        nullable=False,
    )
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_agent_settlements_bot"),
        nullable=False,
    )
    previous_equity = Column(DECIMAL(30, 12), nullable=False, comment="Equity de la liquidación anterior")
    trading_result = Column(
        DECIMAL(30, 12), nullable=False, comment="Ventas menos compras menos comisiones desde la anterior"
    )
    equity_before = Column(DECIMAL(30, 12), nullable=False, comment="Equity antes de las entradas")
    units_before = Column(DECIMAL(30, 12), nullable=False)
    nav = Column(DECIMAL(30, 12), nullable=False, comment="Valor de una unidad en esta liquidación")
    allocated_amount = Column(DECIMAL(30, 12), nullable=False, comment="Dinero que entró")
    units_issued = Column(DECIMAL(30, 12), nullable=False)
    equity_after = Column(DECIMAL(30, 12), nullable=False)
    units_after = Column(DECIMAL(30, 12), nullable=False)
    last_fill_id = Column(BigInteger, nullable=False, comment="Último fill contabilizado")
    fills_count = Column(Integer, nullable=False, server_default=text("'0'"))
    redeemed_amount = Column(
        DECIMAL(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
        comment="Dinero que salió (F5)",
    )
    units_redeemed = Column(
        DECIMAL(30, 12), nullable=False, server_default=text("'0.000000000000'")
    )
    fees_total = Column(
        DECIMAL(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
        comment="Comisiones cobradas en las salidas",
    )
    funding_total = Column(
        DECIMAL(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
        comment="Funding de perpetuos incluido en el resultado",
    )
    unvalued_fees = Column(
        JSON, nullable=False, comment="Comisiones en otra moneda, sin valorar: {asset: monto}"
    )
    note = Column(String(500), nullable=True)
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_agent_settlements_created_by", ondelete="SET NULL"),
        nullable=True,
    )
    settled_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )


class UnitLotModel(Base):
    """Unidades de una persona en un agente, compradas en una liquidación."""

    __tablename__ = "unit_lots"
    __table_args__ = (
        Index("idx_unit_lots_pool_acquired", "pool_id", "acquired_at"),
        Index("idx_unit_lots_user_acquired", "user_id", "acquired_at"),
        CheckConstraint(
            "`units` > 0 AND `units_remaining` >= 0 AND `units_remaining` <= `units`",
            name="chk_unit_lots_units",
        ),
        CheckConstraint("`cost` > 0 AND `nav_at_entry` > 0", name="chk_unit_lots_cost"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pool_id = Column(
        BigInteger,
        ForeignKey("agent_pools.id", name="fk_unit_lots_pool"),
        nullable=False,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_unit_lots_user"),
        nullable=False,
    )
    units = Column(DECIMAL(30, 12), nullable=False, comment="Unidades compradas")
    units_remaining = Column(DECIMAL(30, 12), nullable=False, comment="Unidades que siguen vivas")
    cost = Column(DECIMAL(30, 12), nullable=False, comment="Lo que se pagó (USDT)")
    nav_at_entry = Column(DECIMAL(30, 12), nullable=False)
    settlement_id = Column(
        BigInteger,
        ForeignKey("agent_settlements.id", name="fk_unit_lots_settlement"),
        nullable=True,
    )
    acquired_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        comment="Desde aquí cuenta la permanencia mínima",
    )


class AllocationOrderModel(Base):
    """Asignación en cola: dinero de una persona a un agente."""

    __tablename__ = "allocation_orders"
    __table_args__ = (
        Index("idx_allocation_orders_pool_status", "pool_id", "status"),
        Index("idx_allocation_orders_user_status", "user_id", "status"),
        CheckConstraint(
            "`status` IN ('queued', 'applied', 'canceled')", name="chk_allocation_orders_status"
        ),
        CheckConstraint(
            "`source_bucket` IN ('pending', 'available')", name="chk_allocation_orders_source"
        ),
        CheckConstraint("`amount` > 0", name="chk_allocation_orders_amount"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pool_id = Column(
        BigInteger,
        ForeignKey("agent_pools.id", name="fk_allocation_orders_pool"),
        nullable=False,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_allocation_orders_user"),
        nullable=False,
    )
    amount = Column(DECIMAL(30, 12), nullable=False)
    source_bucket = Column(String(16), nullable=False, comment="De qué saldo sale: pending | available")
    status = Column(
        String(16),
        nullable=False,
        server_default=text("'queued'"),
        comment="queued | applied | canceled",
    )
    note = Column(String(500), nullable=True, comment="Motivo si se canceló")
    settlement_id = Column(
        BigInteger,
        ForeignKey("agent_settlements.id", name="fk_allocation_orders_settlement"),
        nullable=True,
    )
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_allocation_orders_created_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    resolved_at = Column(TIMESTAMP(fsp=6), nullable=True)
