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

// ======================================================================
// Backtesting (sin IA)
// ======================================================================

type BacktestInput = {
	strategy_id: number;
	symbol_id: number;
	timeframe_id: number;
	/** 300–3000. */
	bars: number;
	initial_capital?: string;
	/** Comisión por lado como fracción (0.001 = 0,1 %). */
	fee_pct?: string;
};

type BacktestTrade = {
	entry_ts: string | null;
	exit_ts: string | null;
	entry_price: number;
	exit_price: number | null;
	qty: number;
	stop_loss: number;
	take_profit: number;
	exit_reason: 'stop_loss' | 'take_profit' | 'end' | null;
	pnl: number;
	return_pct: number;
};

/** Fracciones (0.05 = 5 %); montos en la moneda de cotización. */
type BacktestReport = {
	strategy_name: string;
	regime_required: string | null;
	from_ts: string | null;
	to_ts: string | null;
	bars: number;
	signals: number;
	skipped_in_position: number;
	initial_capital: number;
	final_capital: number;
	return_pct: number | null;
	buy_and_hold_pct: number | null;
	risk_pct: number;
	fee_pct: number;
	sl_atr: number;
	tp_atr: number;
	trades: number;
	wins: number;
	losses: number;
	win_rate: number | null;
	profit_factor: number | null;
	payoff_ratio: number | null;
	avg_return_pct: number | null;
	max_drawdown: number;
	total_fees: number;
	equity_curve: { ts: string | null; capital: number }[];
	/** La más reciente primero. */
	closed_trades: BacktestTrade[];
};

/** Trae la historia del exchange y simula: puede tardar unos segundos. */
function runBacktest(input: BacktestInput) {
	return api.post<BacktestReport>('/backtests', input);
}

export type {
	BacktestInput,
	BacktestReport,
	BacktestTrade,
	Strategy,
	StrategyInput,
	StrategyParameters,
	StrategyType,
	StrategyUpdate,
};
export {
	createStrategy,
	getStrategy,
	listStrategies,
	runBacktest,
	updateStrategy,
};
