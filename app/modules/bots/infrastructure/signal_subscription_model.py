# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/signal_subscription_model.py
#
# Modelo SQLAlchemy para la tabla `signal_subscriptions`: un usuario
# sigue las señales de un agente compartido (las recibe por Telegram, sin
# ejecutarlas). Si se borra el agente o el usuario, se borra la
# suscripción.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class SignalSubscriptionModel(Base):
    """Suscripción de un usuario a las señales de un agente."""

    __tablename__ = "signal_subscriptions"
    __table_args__ = (
        UniqueConstraint("bot_id", "user_id", name="uq_signal_subscriptions_bot_user"),
        Index("idx_signal_subscriptions_user", "user_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_signal_subscriptions_bot", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_signal_subscriptions_user", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
