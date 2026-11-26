# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/services/recommendations/generate_market_recommendations_service.py
#
# PROPÓSITO:
# - Pedirle a la IA en qué mercados conviene crear un agente, y con qué
#   estrategia, a partir del ranking del explorador (M2) y de las
#   estrategias disponibles (M5). Guarda el resultado con su historial.
#
# FLUJO:
#   1. Candidatos (Python): mercados del explorador con datos y que NO son
#      bajistas (la app solo abre compras). Máximo _MAX_CANDIDATES.
#   2. Estrategias (Python): la versión más alta de cada nombre, coherente
#      y que no sea bajista (trend_down).
#   3. IA: recibe candidatos + estrategias + reglas y devuelve JSON.
#   4. Filtro determinista (Python): se descarta toda recomendación cuyo
#      símbolo no sea candidato, cuya estrategia no exista o cuyo régimen
#      no encaje con la tendencia del mercado. La IA solo elige dentro de
#      lo que el sistema ya considera válido.
#
# NOTAS:
# - La tendencia del explorador es diaria y las estrategias operan en
#   1h/4h: la recomendación es contexto para elegir mercado, no una señal.
#   Cada operación del agente pasa igual por régimen, reglas, 1 % y 2:1.
# - El prompt va en inglés (como el del agente); los textos para la UI
#   (`summary`, `reasoning`, `risks`) se piden en español.
# ======================================================================

from __future__ import annotations

import logging
import math
from typing import Any

from app.common.contracts import ServiceResult
from app.modules.agent.domain.market_recommendation_entity import (
    MarketRecommendation,
    RecommendationItem,
)
from app.modules.agent.domain.market_recommendation_repository import (
    MarketRecommendationRepository,
)
from app.modules.agent.llm.json_response import parse_json_object
from app.modules.agent.llm.llm_client import LLMCallError, LLMClient, LLMParseError
from app.modules.market.services.explorer import ListTrendExplorerService, TrendRow
from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.domain.strategy_repository import StrategyRepository

logger = logging.getLogger(__name__)

_MAX_CANDIDATES = 30
_MIN_ITEMS = 3
_MAX_ITEMS = 5
_MAX_TEXT = 600
_MAX_SUMMARY = 1000

# Tendencia del explorador → régimen de estrategia que la puede operar.
# None en la estrategia = opera en cualquier régimen.
_REGIME_FOR_DIRECTION = {"up": "trend_up", "sideways": "sideways"}

_SYSTEM_PROMPT = f"""You are a senior trading analyst helping a team decide on which markets to create automated trading agents.

You receive:
- CANDIDATES: markets ranked by daily trend strength, with 24h live stats. Only long (buy) trades are allowed, so bearish markets were already removed.
- STRATEGIES: the strategies an agent can run. Each one declares the market regime it trades (trend_up or sideways) and its timeframe.
- RULES the agents always enforce: max 1% of capital at risk per trade, minimum 2:1 reward/risk, long only, perpetual futures without leverage.

Your job:
1. Pick between {_MIN_ITEMS} and {_MAX_ITEMS} candidates where creating an agent makes the most sense now.
2. For each pick, choose ONE strategy whose regime matches the market direction: direction "up" → a trend_up strategy; direction "sideways" → a sideways strategy. Strategies with regime "any" fit both.
3. Prefer strong, clean trends (high strength, ADX and efficiency), enough 24h liquidity (volume) and moderate volatility (ATR%). Avoid overextended moves after a large 24h spike.
4. Diversify across asset classes when the data allows it. Never recommend the same symbol twice.
5. Be cautious and factual: no guarantees, no hype.

Use ONLY symbol_id and strategy_id values from the lists provided.
Write "summary", "reasoning" and "risks" in neutral Spanish (tuteo), concise and without markdown.

You MUST respond ONLY with valid JSON. No markdown, no text outside the JSON:
{{
  "summary": "<2-3 sentences: general reading of the market right now>",
  "recommendations": [
    {{
      "symbol_id": <int>,
      "strategy_id": <int>,
      "confidence": <float between 0.0 and 1.0>,
      "reasoning": "<1-2 sentences: why this market and this strategy>",
      "risks": "<1 sentence: what could go wrong>"
    }}
  ]
}}"""


class GenerateMarketRecommendationsService:
    """
    Recomendaciones de la IA sobre dónde crear agentes.

    Reglas:
    - Solo mercados alcistas o laterales (la app no abre cortos).
    - La estrategia sugerida debe existir y su régimen encajar con la
      tendencia del mercado; si no, la recomendación se descarta.
    - Si ninguna recomendación sobrevive al filtro, no se guarda nada.
    """

    def __init__(
        self,
        explorer_service: ListTrendExplorerService,
        strategy_repo: StrategyRepository,
        recommendation_repo: MarketRecommendationRepository,
        llm_client: LLMClient,
    ):
        self._explorer = explorer_service
        self._strategy_repo = strategy_repo
        self._repo = recommendation_repo
        self._llm = llm_client

    def generate(
        self, user_id: int, asset_class: str | None = None
    ) -> ServiceResult[MarketRecommendation]:
        explorer = self._explorer.list(asset_class=asset_class)
        if not explorer.success:
            return ServiceResult.fail(
                code=explorer.error.code, http_status=explorer.error.http_status
            )

        candidates = [
            row for row in explorer.data
            if row.metrics is not None and row.metrics.direction in _REGIME_FOR_DIRECTION
        ][:_MAX_CANDIDATES]
        if not candidates:
            return ServiceResult.fail(code="RECOMMENDATION_NO_CANDIDATES", http_status=422)

        strategies = _eligible_strategies(self._strategy_repo.list_all())
        if not strategies:
            return ServiceResult.fail(code="RECOMMENDATION_NO_STRATEGIES", http_status=422)

        snapshot = {
            "asset_class": asset_class,
            "candidates": [_candidate_to_dict(row) for row in candidates],
            "strategies": [_strategy_to_dict(s) for s in strategies],
        }

        try:
            completion = self._llm.complete(
                system_prompt=_SYSTEM_PROMPT,
                user_message=_build_user_message(snapshot),
            )
        except LLMCallError as exc:
            logger.error("[recommendations] falló la llamada al LLM: %s", exc)
            return ServiceResult.fail(
                code="RECOMMENDATION_LLM_CALL_FAILED",
                http_status=502,
                meta={"detail": str(exc)},
            )

        llm_call = {
            "llm_provider": completion.provider,
            "llm_model": completion.model,
            "llm_latency_ms": completion.latency_ms,
        }
        try:
            data = parse_json_object(completion.text)
        except LLMParseError as exc:
            logger.error("[recommendations] respuesta inválida de %s: %s", completion.provider, exc)
            return ServiceResult.fail(
                code="RECOMMENDATION_LLM_PARSE_ERROR",
                http_status=502,
                meta={"raw": completion.text[:500], **llm_call},
            )

        items = _validate_items(data.get("recommendations"), candidates, strategies)
        if not items:
            logger.warning(
                "[recommendations] ninguna recomendación válida de %s: %s",
                completion.provider,
                completion.text[:500],
            )
            return ServiceResult.fail(
                code="RECOMMENDATION_EMPTY",
                http_status=502,
                meta={"raw": completion.text[:500], **llm_call},
            )

        try:
            saved = self._repo.create(
                MarketRecommendation(
                    id=None,
                    created_by_user_id=user_id,
                    asset_class=asset_class,
                    summary=_clean_text(data.get("summary"), _MAX_SUMMARY),
                    items=items,
                    market_snapshot=snapshot,
                    **llm_call,
                )
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise

        return ServiceResult.ok(data=saved)


# ======================================================================
# Helpers
# ======================================================================

def _version_key(version: str) -> tuple:
    """'1.10.0' > '1.9.0': compara por números; lo no numérico cuenta 0."""
    parts = []
    for part in str(version).split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _eligible_strategies(strategies: list[Strategy]) -> list[Strategy]:
    """La versión más alta de cada nombre, válida, coherente y sin régimen bajista."""
    latest: dict[str, Strategy] = {}
    for strategy in strategies:
        current = latest.get(strategy.name)
        if current is None or _version_key(strategy.version) > _version_key(current.version):
            latest[strategy.name] = strategy
    return [
        s for s in latest.values()
        if s.is_valid_type() and s.is_coherent() and s.regime_required != "trend_down"
    ]


def _fits(strategy: Strategy, direction: str) -> bool:
    regime = strategy.regime_required
    return regime is None or regime == _REGIME_FOR_DIRECTION.get(direction)


def _round(value: float | None, digits: int = 4) -> float | None:
    return round(value, digits) if value is not None else None


def _candidate_to_dict(row: TrendRow) -> dict[str, Any]:
    m, t = row.metrics, row.ticker
    return {
        "symbol_id": row.symbol.id,
        "symbol": row.symbol.symbol,
        "asset_class": row.symbol.asset_class,
        "is_perpetual": row.is_perpetual,
        "direction": m.direction,
        "strength": m.strength,
        "adx_14": _round(m.adx_14, 2),
        "efficiency_30": _round(m.efficiency_30),
        "ret_30d": _round(m.ret_30d),
        "ret_90d": _round(m.ret_90d),
        "atr_pct_14": _round(m.atr_pct_14),
        "price": t.last if t else m.last_close,
        "change_24h": _round(t.change_24h) if t else None,
        "volume_24h": round(t.quote_volume_24h) if t and t.quote_volume_24h is not None else None,
    }


def _strategy_to_dict(strategy: Strategy) -> dict[str, Any]:
    return {
        "id": strategy.id,
        "name": strategy.name,
        "version": strategy.version,
        "type": strategy.strategy_type,
        "regime": strategy.regime_required,
        "timeframe": strategy.timeframe_code,
    }


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:+.1f}%"


def _unsigned_pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def _num(value: float | None, digits: int = 1) -> str:
    return "N/A" if value is None else f"{value:.{digits}f}"


def _build_user_message(snapshot: dict[str, Any]) -> str:
    candidate_lines = "\n".join(
        f"- symbol_id={c['symbol_id']} | {c['symbol']} | class={c['asset_class']}"
        f"{' (perpetual)' if c['is_perpetual'] else ''} | direction={c['direction']}"
        f" | strength={_num(c['strength'], 0)} | ADX={_num(c['adx_14'])}"
        f" | efficiency={_num(c['efficiency_30'], 2)} | ret30d={_pct(c['ret_30d'])}"
        f" | ret90d={_pct(c['ret_90d'])} | ATR%={_unsigned_pct(c['atr_pct_14'])}"
        f" | change24h={_pct(c['change_24h'])}"
        f" | volume24h_usdt={c['volume_24h'] if c['volume_24h'] is not None else 'N/A'}"
        for c in snapshot["candidates"]
    )
    strategy_lines = "\n".join(
        f"- strategy_id={s['id']} | {s['name']} v{s['version']} | type={s['type']}"
        f" | regime={s['regime'] or 'any'} | timeframe={s['timeframe'] or 'N/A'}"
        for s in snapshot["strategies"]
    )
    return (
        f"=== MARKET RECOMMENDATION REQUEST ===\n"
        f"ASSET CLASS FILTER: {snapshot['asset_class'] or 'all'}\n\n"
        f"=== CANDIDATES (daily trend + 24h stats) ===\n{candidate_lines}\n\n"
        f"=== STRATEGIES ===\n{strategy_lines}\n\n"
        f"Recommend between {_MIN_ITEMS} and {_MAX_ITEMS} markets "
        f"(fewer if there are not enough good candidates)."
    )


def _clean_text(value: object, limit: int = _MAX_TEXT) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number


def _confidence(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and 0.0 <= number <= 1.0 else None


def _validate_items(
    raw_items: object,
    candidates: list[TrendRow],
    strategies: list[Strategy],
) -> list[RecommendationItem]:
    """Filtro determinista: solo pasa lo que el sistema ya considera válido."""
    if not isinstance(raw_items, list):
        return []

    by_symbol = {row.symbol.id: row for row in candidates}
    by_strategy = {s.id: s for s in strategies}
    items: list[RecommendationItem] = []
    seen: set[int] = set()

    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        row = by_symbol.get(_to_int(raw.get("symbol_id")))
        strategy = by_strategy.get(_to_int(raw.get("strategy_id")))
        if row is None or strategy is None or row.symbol.id in seen:
            continue
        if not _fits(strategy, row.metrics.direction):
            continue
        reasoning = _clean_text(raw.get("reasoning"))
        if not reasoning:
            continue

        seen.add(row.symbol.id)
        items.append(
            RecommendationItem(
                symbol_id=row.symbol.id,
                symbol=row.symbol.symbol,
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                strategy_version=strategy.version,
                timeframe=strategy.timeframe_code,
                confidence=_confidence(raw.get("confidence")),
                reasoning=reasoning,
                risks=_clean_text(raw.get("risks")),
            )
        )
        if len(items) >= _MAX_ITEMS:
            break
    return items
