# -*- coding: utf-8 -*-

"""baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-07

MOTIVO:
- Punto de partida de Alembic. Representa el esquema que ya existía antes
  de adoptar Alembic: `.claude/db_schema.sql` + `migrations/*.sql` (legacy,
  hasta m10_billing.sql inclusive).
- No ejecuta nada. Una BD existente se marca con `alembic stamp 0001_baseline`
  (sin correr upgrade) y a partir de ahí todo cambio va en una revisión nueva.
"""

from __future__ import annotations

from typing import Sequence

revision: str = "0001_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
