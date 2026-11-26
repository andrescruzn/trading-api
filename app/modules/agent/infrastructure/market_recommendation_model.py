# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/market_recommendation_model.py
#
# Modelo SQLAlchemy para la tabla `market_recommendations`: historial de
# recomendaciones de mercados que dio la IA en el explorador.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, ForeignKey, Index, Integer, JSON, String, Text, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class MarketRecommendationORM(Base):
    """Modelo SQLAlchemy para la tabla `market_recommendations`."""

    __tablename__ = "market_recommendations"
    __table_args__ = (
        Index("idx_market_recommendations_created", "created_at"),
        CheckConstraint("json_valid(`items`)", name="chk_market_recommendations_items_json"),
        CheckConstraint(
            "json_valid(`market_snapshot`)",
            name="chk_market_recommendations_snapshot_json",
        ),
        CheckConstraint(
            "`asset_class` IS NULL OR `asset_class` IN "
            "('crypto', 'metal', 'commodity', 'index', 'etf', 'stock', 'forex')",
            name="chk_market_recommendations_asset_class",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_market_recommendations_user", ondelete="SET NULL"),
        nullable=True,
        comment="Super admin que pidió la recomendación",
    )
    asset_class = Column(
        String(16),
        nullable=True,
        comment="Filtro de clase de activo usado; NULL = todas",
    )
    summary = Column(Text, nullable=False, comment="Lectura general del mercado que dio la IA")
    items = Column(
        JSON,
        nullable=False,
        comment="Recomendaciones validadas: símbolo, estrategia, confianza, razonamiento, riesgos",
    )
    market_snapshot = Column(
        JSON,
        nullable=False,
        comment="Métricas de los mercados y estrategias enviadas a la IA (auditoría)",
    )
    llm_provider = Column(String(32), nullable=True, comment="Servicio LLM que respondió (groq, gemini, ollama)")
    llm_model = Column(String(128), nullable=True, comment="Modelo LLM que respondió")
    llm_latency_ms = Column(Integer, nullable=True, comment="Duración de la consulta al LLM en ms (incluye el failover)")
