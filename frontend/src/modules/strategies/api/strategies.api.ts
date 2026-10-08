import type { Regime } from '@/modules/features/lib/regime';
import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type StrategyType = 'trend_following' | 'mean_reversion';

/**
 * `parameters` es JSON libre en el backend; estos son los campos que usa el
 * sistema (ver `CreateStrategyRequest`). Las reglas tienen forma libre.
 */
type StrategyParameters = {
	strategy_type?: StrategyType;
	regime_required?: Regime | null;
	timeframe_code?: string | null;
	/** Fracción del capital (0.01 = 1 %). */
	risk_pct?: number;
	rules?: Record<string, unknown>[];
	[key: string]: unknown;
};

type Strategy = {
	id: number;
	name: string;
	version: string;
	description: string | null;
	parameters: StrategyParameters;
	created_at: string | null;
};

type StrategyInput = {
	name: string;
	version: string;
	description: string | null;
	parameters: StrategyParameters;
};

/** En el PUT, `description: null` deja la actual; `''` la borra. */
type StrategyUpdate = Partial<StrategyInput>;

function listStrategies() {
	return api.get<Strategy[]>('/strategies');
}

function getStrategy(id: number) {
	return api.get<Strategy>(`/strategies/${id}`);
}

/** Solo admin. */
function createStrategy(input: StrategyInput) {
	return api.post<Strategy>('/strategies', input);
}

/** Solo admin. */
function updateStrategy(id: number, input: StrategyUpdate) {
	return api.put<Strategy>(`/strategies/${id}`, input);
}

export type {
	Strategy,
	StrategyInput,
	StrategyParameters,
	StrategyType,
	StrategyUpdate,
};
export { createStrategy, getStrategy, listStrategies, updateStrategy };
