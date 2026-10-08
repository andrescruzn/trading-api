# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/order_model.py
#
# Modelo SQLAlchemy para la tabla `orders`.
# Mapea directamente las columnas de la BD — sin lógica de negocio.
#
# NOTA: `meta` no tiene DEFAULT en MySQL (JSON); el `default=dict` es del
# lado Python para que un INSERT sin meta no falle.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    JSON,
    NUMERIC,
    String,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class OrderModel(Base):
    """Modelo SQLAlchemy para la tabla `orders`."""

    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_bot_ts", "bot_id", "ts"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_signal", "signal_id"),
        Index("idx_orders_exchange_order_id", "exchange_order_id"),
        CheckConstraint("json_valid(`meta`)", name="chk_orders_meta_json"),
        # market → sin precios; limit → price obligatorio; stop/stop_limit → stop_price obligatorio
        CheckConstraint(
            "(`type` = 'market' AND `price` IS NULL AND `stop_price` IS NULL)"
            " OR (`type` = 'limit' AND `price` IS NOT NULL AND `stop_price` IS NULL)"
            " OR (`type` IN ('stop', 'stop_limit') AND `stop_price` IS NOT NULL)",
            name="chk_orders_price_logic",
        ),
        CheckConstraint("`qty` > 0", name="chk_orders_qty"),
        CheckConstraint("`side` IN ('buy', 'sell')", name="chk_orders_side"),
        CheckConstraint(
            "`status` IN ('new', 'sent', 'partially_filled', 'filled', 'canceled', 'rejected')",
            name="chk_orders_status",
        ),
        CheckConstraint(
            "`type` IN ('market', 'limit', 'stop', 'stop_limit')",
            name="chk_orders_type",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Relaciones
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_orders_bot"),
        nullable=False,
    )
    signal_id = Column(
        BigInteger,
        ForeignKey("signals.id", name="fk_orders_signal"),
        nullable=True,
    )

    # Identificador externo del exchange (ej: "1234567890" de Binance)
    exchange_order_id = Column(String(128), nullable=True)

    # Timestamp de la orden (cuándo fue creada la intención de operar)
    ts = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    # Características de la orden
    side = Column(String(8), nullable=False)          # buy | sell
    type = Column(String(16), nullable=False)         # market | limit | stop | stop_limit
    status = Column(String(20), nullable=False, server_default=text("'new'"))

    # Cantidades y precios (NUMERIC(30,12) para precisión financiera)
    qty = Column(NUMERIC(30, 12), nullable=False)
    price = Column(NUMERIC(30, 12), nullable=True)       # None para market orders
    stop_price = Column(NUMERIC(30, 12), nullable=True)  # para stop y stop_limit

    # Opcionales
    time_in_force = Column(String(8), nullable=True)     # GTC, IOC, FOK
    meta = Column(JSON, nullable=False, default=dict)

    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
