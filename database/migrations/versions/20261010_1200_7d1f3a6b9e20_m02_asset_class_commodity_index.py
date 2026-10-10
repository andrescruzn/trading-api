"""m02 asset_class commodity index

Revision ID: 7d1f3a6b9e20
Revises: 5b7e2a9c41d3
Create Date: 2026-10-10 12:00:00.000000+00:00

MOTIVO:
- M2 (Market Data): se abren los perpetuos TradFi de Binance/Bybit
  (oro, plata, petróleo, gas, cobre, ETFs y acciones). Petróleo, gas y
  cobre no son metales preciosos ni cripto: `symbols.asset_class` admite
  ahora `commodity` (materias primas) e `index` (índices).
- Autogenerate no detecta cambios en un CHECK de una tabla existente:
  se reemplaza a mano.
- Paso de datos: se desactivan los símbolos que nunca reciben velas
  (los de TradingView, `data_vendor` sin descarga automática) y
  `MATIC/USDT` (renombrado a POL; ccxt ya no lo encuentra).
- El downgrade reactiva esos símbolos y pasa los `commodity`/`index` a
  `metal`/`etf` antes de restaurar el CHECK anterior, para que no falle.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '7d1f3a6b9e20'
down_revision: str | Sequence[str] | None = '5b7e2a9c41d3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHECK = 'chk_symbols_asset_class'
_NEW = "`asset_class` IN ('crypto', 'metal', 'commodity', 'index', 'etf', 'stock', 'forex')"
_OLD = "`asset_class` IN ('crypto', 'metal', 'etf', 'stock', 'forex')"

# Símbolos que nunca reciben velas: TradingView (sin fetcher) y MATIC (ahora POL)
_DEAD_SYMBOLS_WHERE = (
    "exchange_id IN (SELECT id FROM exchanges WHERE name = 'TradingView') "
    "OR (symbol = 'MATIC/USDT' "
    "AND exchange_id IN (SELECT id FROM exchanges WHERE name = 'Binance'))"
)


def upgrade() -> None:
    op.drop_constraint(_CHECK, 'symbols', type_='check')
    op.create_check_constraint(_CHECK, 'symbols', _NEW)

    # MySQL no deja leer en un subquery la tabla que se actualiza;
    # aquí se leen `exchanges`, no `symbols`, así que es válido.
    op.execute(sa.text(f"UPDATE symbols SET is_active = 0 WHERE {_DEAD_SYMBOLS_WHERE}"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE symbols SET asset_class = 'metal' WHERE asset_class = 'commodity'"))
    op.execute(sa.text("UPDATE symbols SET asset_class = 'etf' WHERE asset_class = 'index'"))
    op.drop_constraint(_CHECK, 'symbols', type_='check')
    op.create_check_constraint(_CHECK, 'symbols', _OLD)

    op.execute(sa.text(f"UPDATE symbols SET is_active = 1 WHERE {_DEAD_SYMBOLS_WHERE}"))
