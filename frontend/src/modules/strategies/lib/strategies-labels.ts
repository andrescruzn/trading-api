import { type Regime, REGIME_OPTIONS } from '@/modules/features/lib/regime';
import type { SelectOption } from '@/modules/shared/components/option-select';
import type { StrategyType } from '@/modules/strategies/api/strategies.api';

const STRATEGY_TYPE_LABELS: Record<StrategyType, string> = {
	trend_following: 'Seguimiento de tendencia',
	mean_reversion: 'Reversión a la media',
};

const STRATEGY_TYPE_OPTIONS: SelectOption[] = Object.entries(
	STRATEGY_TYPE_LABELS,
).map(([value, label]) => ({ value, label }));

/** Valor del select para `regime_required: null` (Base UI usa `null` como "sin selección"). */
const ANY_REGIME = 'any';

const REGIME_REQUIRED_OPTIONS: SelectOption[] = [
	{ value: ANY_REGIME, label: 'Sin restricción' },
	...REGIME_OPTIONS,
];

/**
 * Filtro de régimen (regla de negocio, igual que `Strategy._ALLOWED_REGIMES`
 * del backend): seguir tendencia solo opera en tendencia; reversión a la
 * media solo en lateral. Sin régimen requerido siempre es coherente.
 */
const ALLOWED_REGIMES: Record<StrategyType, Regime[]> = {
	trend_following: ['trend_up', 'trend_down'],
	mean_reversion: ['sideways'],
};

function isRegimeCoherent(type: string | null, regime: string | null): boolean {
	if (!type || !regime || regime === ANY_REGIME) return true;
	const allowed = ALLOWED_REGIMES[type as StrategyType];
	return !allowed || allowed.includes(regime as Regime);
}

/** Texto de ayuda cuando el tipo y el régimen no son compatibles. */
function regimeCoherenceHint(type: string | null): string {
	return type === 'mean_reversion'
		? 'Reversión a la media solo opera en régimen lateral.'
		: 'Seguimiento de tendencia solo opera en tendencia alcista o bajista.';
}

function strategyTypeLabel(type: string | null | undefined): string {
	if (!type) return '—';
	return STRATEGY_TYPE_LABELS[type as StrategyType] ?? type;
}

const OPERATOR_SYMBOLS: Record<string, string> = {
	lt: '<',
	lte: '≤',
	gt: '>',
	gte: '≥',
	eq: '=',
	neq: '≠',
};

/** `{indicator: 'rsi_14', operator: 'lt', value: 30}` → `rsi_14 < 30`. */
function describeRule(rule: Record<string, unknown>): string {
	const { indicator, operator, value } = rule;
	if (typeof indicator !== 'string' || typeof operator !== 'string') {
		return JSON.stringify(rule);
	}
	const shownValue =
		value !== null && typeof value === 'object'
			? JSON.stringify(value)
			: String(value ?? '—');
	return `${indicator} ${OPERATOR_SYMBOLS[operator] ?? operator} ${shownValue}`;
}

// `risk_pct` viaja como fracción (0.01) y en la UI se edita en % (1). Se
// redondea para no arrastrar ruido de coma flotante (0.007 * 100 = 0.7000…1).
function fractionToPercent(fraction: number): number {
	return Math.round(fraction * 100 * 10000) / 10000;
}

function percentToFraction(percent: number): number {
	return Math.round((percent / 100) * 1_000_000) / 1_000_000;
}

/** Regla del 1 %: nunca arriesgar más del 1 % del capital por operación. */
const MAX_RISK_PERCENT = 1;

export {
	ALLOWED_REGIMES,
	ANY_REGIME,
	describeRule,
	fractionToPercent,
	isRegimeCoherent,
	MAX_RISK_PERCENT,
	percentToFraction,
	REGIME_REQUIRED_OPTIONS,
	regimeCoherenceHint,
	STRATEGY_TYPE_LABELS,
	STRATEGY_TYPE_OPTIONS,
	strategyTypeLabel,
};
