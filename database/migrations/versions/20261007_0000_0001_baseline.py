# -*- coding: utf-8 -*-

"""baseline

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-07

MOTIVO:
- Punto de partida de Alembic. No ejecuta nada.
- El esquema completo lo crea la revisión siguiente ("esquema inicial"),
  generada con --autogenerate desde los modelos ORM.
- Una BD que ya tenía el esquema antes de Alembic se marca con
  `alembic stamp head` (sin correr upgrade).
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
