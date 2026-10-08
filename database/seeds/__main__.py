# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/__main__.py
#
# PROPÓSITO:
# - Runner de seeds. Ejecuta los seeds indicados (o todos, en orden de
#   dependencias) contra la BD del .env.
#
# USO:
#   uv run python -m database.seeds                      # todos
#   uv run python -m database.seeds roles market_data    # solo esos
#   uv run python -m database.seeds --list               # ver los disponibles
#
# NOTAS:
# - Cada seed es idempotente: se puede correr varias veces.
# - Un commit por seed: si uno falla, se revierte solo ese y se detiene.
# ======================================================================

from __future__ import annotations

import sys
from typing import Callable

from sqlalchemy.orm import Session

import app.extensions.db.models_registry  # noqa: F401  (registra los modelos y sus FKs)
from app.extensions.db import SessionLocal, SqlAlchemyRepository
from database.seeds import accounts, market_data, roles, strategies
from database.seeds._helpers import SeedStats

# Orden de dependencias: accounts necesita exchanges (market_data) y usuarios.
SEEDS: dict[str, Callable[[Session], SeedStats]] = {
    "roles": roles.run,
    "market_data": market_data.run,
    "strategies": strategies.run,
    "accounts": accounts.run,
}


def main(argv: list[str]) -> int:
    if "--list" in argv:
        print("\n".join(SEEDS))
        return 0

    unknown = [name for name in argv if name not in SEEDS]
    if unknown:
        print(f"Seeds desconocidos: {', '.join(unknown)}. Disponibles: {', '.join(SEEDS)}")
        return 1

    selected = [name for name in SEEDS if not argv or name in argv]

    session = SessionLocal()
    repo = SqlAlchemyRepository(session)
    try:
        for name in selected:
            try:
                stats = SEEDS[name](session)
                repo.commit()
            except Exception:
                repo.rollback()
                print(f"[{name}] ERROR: se revirtió este seed")
                raise
            print(f"[{name}]\n{stats.summary() or 'sin cambios'}\n")
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
