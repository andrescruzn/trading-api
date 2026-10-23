# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/platform_wallet_repository_impl.py
#
# Implementaciones SQLAlchemy de los repositorios de la billetera de la
# plataforma y de sus fotos de saldo.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.common.utils import ensure_aware_utc
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.accounts.domain.platform_wallet_entity import PlatformWallet
from app.modules.accounts.domain.platform_wallet_repository import (
    PlatformWalletRepository,
    WalletSnapshotRepository,
)
from app.modules.accounts.domain.wallet_snapshot_entity import WalletAssetLine, WalletSnapshot
from app.modules.accounts.infrastructure.platform_wallet_model import (
    PlatformWalletModel,
    WalletSnapshotModel,
)

# La tabla tiene una sola fila, siempre con este id (CHECK en la tabla)
_WALLET_ROW_ID = 1


class SqlAlchemyPlatformWalletRepository(SqlAlchemyRepository, PlatformWalletRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: PlatformWalletModel) -> PlatformWallet:
        return PlatformWallet(
            account_id=model.account_id,
            base_asset=model.base_asset,
            # MySQL devuelve TIMESTAMP sin zona: se marcan como UTC
            last_synced_at=ensure_aware_utc(model.last_synced_at),
            last_sync_error=model.last_sync_error,
            updated_by_user_id=model.updated_by_user_id,
            updated_at=ensure_aware_utc(model.updated_at),
        )

    def get(self) -> PlatformWallet | None:
        model = self._session.get(PlatformWalletModel, _WALLET_ROW_ID)
        return None if model is None else self._to_domain(model)

    def save(self, wallet: PlatformWallet) -> PlatformWallet:
        model = self._session.get(PlatformWalletModel, _WALLET_ROW_ID)
        if model is None:
            model = PlatformWalletModel(id=_WALLET_ROW_ID)
            self._session.add(model)
        model.account_id = wallet.account_id
        model.base_asset = wallet.base_asset
        model.last_synced_at = wallet.last_synced_at
        model.last_sync_error = wallet.last_sync_error
        model.updated_by_user_id = wallet.updated_by_user_id
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)


# ======================================================================
# Fotos de saldo
# ======================================================================

def _decimal_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _line_to_json(line: WalletAssetLine) -> dict[str, str | None]:
    # Decimales como texto: el JSON no pierde precisión
    return {
        "asset":  line.asset,
        "free":   str(line.free),
        "locked": str(line.locked),
        "price":  None if line.price is None else str(line.price),
        "value":  None if line.value is None else str(line.value),
    }


def _line_from_json(item: dict[str, Any]) -> WalletAssetLine:
    return WalletAssetLine(
        asset=str(item["asset"]),
        free=Decimal(str(item["free"])),
        locked=Decimal(str(item["locked"])),
        price=_decimal_or_none(item.get("price")),
        value=_decimal_or_none(item.get("value")),
    )


class SqlAlchemyWalletSnapshotRepository(SqlAlchemyRepository, WalletSnapshotRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: WalletSnapshotModel) -> WalletSnapshot:
        return WalletSnapshot(
            id=model.id,
            account_id=model.account_id,
            base_asset=model.base_asset,
            total_value=Decimal(str(model.total_value)),
            free_value=Decimal(str(model.free_value)),
            locked_value=Decimal(str(model.locked_value)),
            source=model.source,
            assets=[_line_from_json(item) for item in (model.assets or [])],
            missing_prices=list(model.missing_prices or []),
            ts=ensure_aware_utc(model.ts),
        )

    def record(self, snapshot: WalletSnapshot) -> WalletSnapshot:
        model = WalletSnapshotModel(
            account_id=snapshot.account_id,
            base_asset=snapshot.base_asset,
            total_value=snapshot.total_value,
            free_value=snapshot.free_value,
            locked_value=snapshot.locked_value,
            source=snapshot.source,
            assets=[_line_to_json(line) for line in snapshot.assets],
            missing_prices=list(snapshot.missing_prices),
        )
        if snapshot.ts is not None:
            model.ts = snapshot.ts
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def get_latest(self, account_id: int) -> WalletSnapshot | None:
        model = (
            self._session.query(WalletSnapshotModel)
            .filter(WalletSnapshotModel.account_id == account_id)
            .order_by(WalletSnapshotModel.ts.desc(), WalletSnapshotModel.id.desc())
            .first()
        )
        return None if model is None else self._to_domain(model)

    def list_by_account(self, account_id: int, limit: int = 50) -> list[WalletSnapshot]:
        models = (
            self._session.query(WalletSnapshotModel)
            .filter(WalletSnapshotModel.account_id == account_id)
            .order_by(WalletSnapshotModel.ts.desc(), WalletSnapshotModel.id.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]
