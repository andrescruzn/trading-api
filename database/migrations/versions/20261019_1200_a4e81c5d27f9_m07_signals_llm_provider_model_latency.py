"""m07 signals llm provider model latency

Revision ID: a4e81c5d27f9
Revises: 7d1f3a6b9e20
Create Date: 2026-10-19 12:00:00.000000+00:00

MOTIVO:
- M6/M7: con el pool rotativo de LLMs (groq, gemini, ollama) cada análisis
  lo puede atender un servicio distinto; hasta ahora solo quedaba en el
  log (`[llm] respondió <servicio>`). Cada señal guarda ahora qué servicio
  y modelo respondieron y cuánto tardó la consulta, para auditar y
  comparar servicios.
- signals.llm_provider VARCHAR(32), signals.llm_model VARCHAR(128),
  signals.llm_latency_ms INT; nullable: las señales rechazadas por
  régimen o reglas no consultan al LLM, y las anteriores no lo tienen.
- Escrita a mano para dejar las columnas después de `features_hash`
  (mismo orden que el modelo); `op.add_column` no admite AFTER.
- El downgrade elimina las tres columnas (se pierde ese dato).
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a4e81c5d27f9'
down_revision: str | Sequence[str] | None = '7d1f3a6b9e20'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE signals "
        "ADD COLUMN llm_provider VARCHAR(32) NULL "
        "COMMENT 'Servicio LLM que respondió (groq, gemini, ollama)' AFTER features_hash, "
        "ADD COLUMN llm_model VARCHAR(128) NULL "
        "COMMENT 'Modelo LLM que respondió' AFTER llm_provider, "
        "ADD COLUMN llm_latency_ms INT NULL "
        "COMMENT 'Duración de la consulta al LLM en ms (incluye el failover)' AFTER llm_model"
    ))


def downgrade() -> None:
    op.drop_column('signals', 'llm_latency_ms')
    op.drop_column('signals', 'llm_model')
    op.drop_column('signals', 'llm_provider')
