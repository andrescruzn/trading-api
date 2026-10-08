import { api } from '@/modules/shared/lib/api-client';

// ======================================================================
// Tipos (reflejan el JSON del backend tal cual, en snake_case)
// ======================================================================

type BotMode = 'paper' | 'live';
type BotStatus = 'running' | 'stopped' | 'paused' | 'error';
type BotTransition = 'start' | 'pause' | 'stop';

type Bot = {
	id: number;
	strategy_id: number;
	symbol_id: number;
	timeframe_id: number;
	account_id: number;
	feature_set_id: number | null;
	mode: BotMode;
	status: BotStatus;
	/** JSON libre; hoy incluye `risk_pct` (fracción, 0.01 = 1 %). */
	risk_params: Record<string, unknown>;
	started_at: string | null;
	stopped_at: string | null;
	created_at: string | null;
};

type BotRiskParams = {
	/** Fracción del capital: 0.01 = 1 %. */
	risk_pct: number;
	max_drawdown_pct?: number;
};

type BotInput = {
	strategy_id: number;
	symbol_id: number;
	timeframe_id: number;
	account_id: number;
	feature_set_id: number;
	mode: BotMode;
	risk_params: BotRiskParams;
};

type SignalAction = 'buy' | 'sell' | 'hold';

/** Códigos con los que el agente explica por qué rechazó la operación. */
type SignalRejectionReason =
	| 'REGIME_MISMATCH'
	| 'RULES_NOT_MET'
	| 'LLM_REJECTED'
	| 'RR_RATIO_TOO_LOW';

type SignalRuleDetail = {
	indicator: string;
	operator: string;
	threshold: unknown;
	actual_value: unknown;
	passed: boolean;
};

/** Resultado completo del análisis del agente (JSON libre en el backend). */
type SignalReasons = {
	decision?: 'APPROVED' | 'REJECTED';
	rejection_reason?: SignalRejectionReason | string | null;
	reasoning?: string;
	regime_check_passed?: boolean;
	rules_check_passed?: boolean;
	rr_check_passed?: boolean;
	rules_detail?: SignalRuleDetail[];
	meta?: Record<string, unknown>;
	[key: string]: unknown;
};

/**
 * Las señales llegan con precios y ratios como `number` (el backend los
 * convierte a float al serializar), no como string.
 */
type Signal = {
	id: number;
	bot_id: number;
	ts: string | null;
	action: SignalAction;
	approved: boolean;
	/** 0–1. */
	confidence: number | null;
	entry_price: number | null;
	stop_loss: number | null;
	take_profit: number | null;
	position_size: number | null;
	rr_ratio: number | null;
	reasons: SignalReasons;
	created_at: string | null;
};

type SignalFilters = {
	bot_id: number;
	action?: SignalAction;
	limit?: number;
};

// ======================================================================
// Bots
// ======================================================================

/**
 * Usuario: el backend exige `account_id` (solo sus bots). Admin: sin filtro
 * devuelve todos.
 */
function listBots(filters: { account_id?: number } = {}) {
	return api.get<Bot[]>('/bots', filters);
}

function getBot(id: number) {
	return api.get<Bot>(`/bots/${id}`);
}

function createBot(input: BotInput) {
	return api.post<Bot>('/bots', input);
}

/** `start`: detenido → activo · `pause`: activo → pausado · `stop`: → detenido. */
function transitionBot(id: number, transition: BotTransition) {
	return api.post<Bot>(`/bots/${id}/${transition}`);
}

// ======================================================================
// Señales
// ======================================================================

/** El backend las devuelve de la más reciente a la más antigua. */
function listSignals(filters: SignalFilters) {
	return api.get<Signal[]>('/signals', filters);
}

/** Invoca al agente de IA (puede tardar). El bot debe estar activo. */
function generateSignal(botId: number) {
	return api.post<Signal>('/signals/generate', { bot_id: botId });
}

export type {
	Bot,
	BotInput,
	BotMode,
	BotRiskParams,
	BotStatus,
	BotTransition,
	Signal,
	SignalAction,
	SignalFilters,
	SignalReasons,
	SignalRejectionReason,
	SignalRuleDetail,
};
export {
	createBot,
	generateSignal,
	getBot,
	listBots,
	listSignals,
	transitionBot,
};
