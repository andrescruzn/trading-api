# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/_helpers.py
#
# PROPÓSITO:
# - Utilidades comunes de los seeds: inserción idempotente por clave natural
#   y conteo de creados / existentes para el resumen.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass
class SeedStats:
    """Cuenta, por tabla, cuántas filas se crearon y cuántas ya existían."""

    created: dict[str, int] = field(default_factory=dict)
    existing: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def track(self, table: str, created: bool) -> None:
        target = self.created if created else self.existing
        target[table] = target.get(table, 0) + 1

    def summary(self) -> str:
        tables = sorted(set(self.created) | set(self.existing))
        lines = [
            f"{t}: {self.created.get(t, 0)} creados, {self.existing.get(t, 0)} ya existían"
            for t in tables
        ]
        return "\n".join(lines + self.notes)


def get_or_create(
    session: Session,
    model: type,
    lookup: dict[str, Any],
    values: dict[str, Any] | None = None,
    stats: SeedStats | None = None,
) -> Any:
    """
    Devuelve la fila que coincide con `lookup` o la crea con `lookup + values`.

    Regla:
    - Nunca actualiza una fila existente (mismo efecto que INSERT IGNORE):
      correr un seed dos veces no cambia datos que alguien editó a mano.
    """
    obj = session.execute(select(model).filter_by(**lookup)).scalar_one_or_none()
    created = obj is None

    if created:
        obj = model(**lookup, **(values or {}))
        session.add(obj)
        session.flush()

    if stats is not None:
        stats.track(model.__tablename__, created)
    return obj
