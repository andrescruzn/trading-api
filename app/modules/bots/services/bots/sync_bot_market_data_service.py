# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/sync_bot_market_data_service.py
#
# PROPÓSITO:
# - Actualizar a pedido los datos de mercado de un agente: descarga las
#   velas de su símbolo y timeframe y recalcula sus indicadores.
#
# NOTAS:
# - El scheduler ya hace esto cada ciclo para los agentes activos; este
#   caso de uso sirve para forzarlo o para preparar un agente detenido.
# - Reutiliza los servicios de M2 (descarga ccxt) y M3 (cálculo), que
#   confirman cada uno su propia escritura: si el cálculo falla, las velas
#   descargadas quedan guardadas, igual que en el scheduler.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.features.services.calculations import CalculateFeaturesService
from app.modules.market.services.candles import FetchCandlesService

# Mismo tamaño que la carga inicial del scheduler: alcanza para la EMA 200.
_FETCH_LIMIT = 500


class SyncBotMarketDataService:
    """
    Descarga las velas y recalcula los indicadores de un agente.

    Reglas:
    - Un usuario solo actualiza agentes de sus cuentas (`owner_id`); uno
      ajeno responde BOT_NOT_FOUND, igual que si no existiera.
    - Sin conjunto de indicadores solo se descargan las velas.
    """

    def __init__(
        self,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
        fetch_candles: FetchCandlesService,
        calculate_features: CalculateFeaturesService,
    ):
        self._bot_repo = bot_repo
        self._account_repo = account_repo
        self._fetch_candles = fetch_candles
        self._calculate_features = calculate_features

    def sync(self, bot_id: int, owner_id: int | None = None) -> ServiceResult[dict]:
        bot = find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        fetched = self._fetch_candles.fetch(
            symbol_id=bot.symbol_id,
            timeframe_id=bot.timeframe_id,
            limit=_FETCH_LIMIT,
        )
        if not fetched.success:
            return fetched

        rows_calculated: int | None = None
        if bot.feature_set_id is not None:
            calculated = self._calculate_features.calculate(
                symbol_id=bot.symbol_id,
                timeframe_id=bot.timeframe_id,
                feature_set_id=bot.feature_set_id,
            )
            if not calculated.success:
                return calculated
            rows_calculated = calculated.data["rows_calculated"]

        return ServiceResult.ok(data={
            "rows_fetched": fetched.data["rows_fetched"],
            "rows_calculated": rows_calculated,
        })
