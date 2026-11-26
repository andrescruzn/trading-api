import type { FeatureSet } from '@/modules/features/api/features.api';
import type { MarketSymbol, Timeframe } from '@/modules/market/api/market.api';
import type { Strategy } from '@/modules/strategies/api/strategies.api';

// Regla del 1 %: nunca arriesgar más del 1 % del capital por operación.
const MAX_RISK_FRACTION = 0.01;

/**
 * Claves de indicadores que piden las reglas de una estrategia. Igual que
 * `rule_keys` del backend: el `indicator` y, si `value` es texto no
 * numérico, el indicador contra el que se compara (`ema_20 > ema_50`).
 */
function strategyRuleKeys(strategy: Strategy): Set<string> {
	const keys = new Set<string>();
	for (const rule of strategy.parameters.rules ?? []) {
		if (typeof rule.indicator === 'string') keys.add(rule.indicator);
		const value = rule.value;
		if (typeof value === 'string' && Number.isNaN(Number(value))) {
			keys.add(value);
		}
	}
	return keys;
}

/** El conjunto calcula todo lo que pide la estrategia (el backend lo vuelve a validar). */
function isFeatureSetCompatible(
	strategy: Strategy,
	featureSet: FeatureSet,
): boolean {
	const outputs = new Set(featureSet.outputs ?? []);
	return [...strategyRuleKeys(strategy)].every((key) => outputs.has(key));
}

/**
 * Conjunto recomendado para una estrategia: el de su mismo enfoque y, si no
 * hay, el más completo (`all`). Solo entre los compatibles.
 */
function recommendedFeatureSet(
	strategy: Strategy,
	compatible: FeatureSet[],
): FeatureSet | null {
	const type = strategy.parameters.strategy_type;
	return (
		compatible.find((featureSet) => featureSet.focus === type) ??
		compatible.find((featureSet) => featureSet.focus === 'all') ??
		compatible[0] ??
		null
	);
}

/** Timeframe que declara la estrategia, resuelto contra el catálogo. */
function strategyTimeframe(
	strategy: Strategy,
	timeframes: Timeframe[] | undefined,
): Timeframe | null {
	const code = strategy.parameters.timeframe_code;
	if (!code) return null;
	return timeframes?.find((timeframe) => timeframe.code === code) ?? null;
}

/** Riesgo por operación de la estrategia (fracción), nunca por encima del 1 %. */
function strategyRiskFraction(strategy: Strategy): number {
	const value = Number(strategy.parameters.risk_pct ?? MAX_RISK_FRACTION);
	if (!Number.isFinite(value) || value <= 0) return MAX_RISK_FRACTION;
	return Math.min(value, MAX_RISK_FRACTION);
}

/** `BTC/USDT · EMA Trend Follower`: nombre sugerido, editable en el último paso. */
function defaultAgentName(
	symbol: MarketSymbol | undefined,
	strategy: Strategy | undefined,
): string {
	return [symbol?.symbol, strategy?.name].filter(Boolean).join(' · ');
}

export {
	defaultAgentName,
	isFeatureSetCompatible,
	MAX_RISK_FRACTION,
	recommendedFeatureSet,
	strategyRiskFraction,
	strategyRuleKeys,
	strategyTimeframe,
};
