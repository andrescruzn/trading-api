# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/order_model.py
#
# Modelo SQLAlchemy para la tabla `orders`.
# Mapea directamente las columnas de la BD — sin lógica de negocio.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, JSON, NUMERIC, String, TIMESTAMP, text

from app.extensions.db import Base


class OrderModel(Base):
    """Modelo SQLAlchemy para la tabla `orders`."""

    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Relaciones
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id"),
        nullable=False,
        index=True,
    )
    signal_id = Column(
        BigInteger,
        ForeignKey("signals.id"),
        nullable=True,
        index=True,
    )

    # Identificador externo del exchange (ej: "1234567890" de Binance)
    exchange_order_id = Column(String(128), nullable=True, index=True)

    # Timestamp de la orden (cuándo fue creada la intención de operar)
    ts = Column(
        TIMESTAMP(6),
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
    meta = Column(JSON, nullable=False, server_default=text("'{}'"))

    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
